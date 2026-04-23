import os
import socket
import qrcode
import base64
import random
import uuid
import logging
import time
from io import BytesIO
from datetime import datetime
from threading import Lock
from flask import Flask, render_template, request, send_file, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
# Generate a secure random key if not provided
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence standard Flask/Werkzeug request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)
logging.getLogger('gevent').setLevel(logging.ERROR)

# Silence Socket.IO logs
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

# In-memory store for Cloud Mode: { code: { sender_sid, receiver_sid, created_at } }
rooms = {}

# Suppress verbose werkzeug logging for frequent endpoints
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# In-memory peer registry (NO FILE STORAGE)
peers = {}  # { device_id: { 'device_name': ..., 'pairing_code': ..., 'timestamp': ... } }
pairing_codes = {}  # { 'pairing_code': device_id } - for quick lookup
peers_lock = Lock()

# WebRTC signaling data (temporary, cleaned up after connection)
signaling_data = {}  # { 'connection_id': { 'offer': ..., 'answer': ..., 'candidates': [...] } }
signaling_lock = Lock()

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def generate_pairing_code():
    """Generate a unique 6-digit pairing code"""
    while True:
        code = f"{random.randint(0, 999999):06d}"
        if code not in pairing_codes:
            return code

def generate_qr_code(data):
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

@app.route('/')
def index():
    """Main page"""
    device_id = session.get('device_id')
    if not device_id:
        device_id = str(uuid.uuid4())[:8]
        session['device_id'] = device_id
        logger.info(f"New device registered: {device_id}")

    return render_template('p2p.html', device_id=device_id)

@app.route('/api/device-info')
def device_info():
    """Get device information"""
    local_ip = get_local_ip()
    device_id = session.get('device_id', 'unknown')
    port = request.host.split(':')[1] if ':' in request.host else '5000'

    return jsonify({
        'ip': local_ip,
        'port': port,
        'device_id': device_id,
        'device_name': f'Device-{device_id}'
    })

@app.route('/api/register-peer', methods=['POST'])
def register_peer():
    """Register a peer for P2P discovery"""
    try:
        device_id = session.get('device_id', str(uuid.uuid4())[:8])
        data = request.json or {}

        # Generate unique 6-digit pairing code
        pairing_code = generate_pairing_code()

        with peers_lock:
            peers[device_id] = {
                'device_name': data.get('device_name', f'Device-{device_id}'),
                'pairing_code': pairing_code,
                'timestamp': datetime.now().isoformat(),
                'client_ip': request.remote_addr,
                'server_port': data.get('port', 5000)
            }
            pairing_codes[pairing_code] = device_id

        logger.info(f"Peer registered: {device_id} (Code: {pairing_code})")
        return jsonify({
            'status': 'registered',
            'device_id': device_id,
            'pairing_code': pairing_code,
            'message': 'Peer registered successfully'
        })
    except Exception as e:
        logger.error(f"Error registering peer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/peers')
def get_peers():
    """Get list of available peers for P2P connection"""
    try:
        current_device = session.get('device_id')

        with peers_lock:
            # Get all peers except current device
            available_peers = {
                device_id: info
                for device_id, info in peers.items()
                if device_id != current_device
            }

        logger.debug(f"Available peers for {current_device}: {len(available_peers)}")
        return jsonify({
            'peers': available_peers,
            'your_device_id': current_device
        })
    except Exception as e:
        logger.error(f"Error getting peers: {e}")
        return jsonify({'error': str(e)}), 500

# Simplified Signaling System
# incoming_signals[to_device_id] = [ {from, type, sdp, candidate}, ... ]
incoming_signals = {}

@app.route('/api/signal', methods=['POST'])
def send_signal():
    """Unified signaling endpoint for offers, answers, and candidates"""
    try:
        data = request.json
        from_device = session.get('device_id')
        to_device = data.get('to')
        
        if not from_device or not to_device:
            return jsonify({'error': 'Missing device ID'}), 400

        signal = {
            'from': from_device,
            'type': data.get('type'),
            'sdp': data.get('sdp'),
            'candidate': data.get('candidate'),
            'timestamp': time.time()
        }

        with signaling_lock:
            if to_device not in incoming_signals:
                incoming_signals[to_device] = []
            
            # Limit mailbox size to prevent memory issues
            if len(incoming_signals[to_device]) > 100:
                incoming_signals[to_device].pop(0)
                
            incoming_signals[to_device].append(signal)

        return jsonify({'status': 'sent'})
    except Exception as e:
        logger.error(f"Signal error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-signals', methods=['GET'])
def get_signals():
    """Retrieve and clear all incoming signals for the current device"""
    try:
        device_id = session.get('device_id')
        if not device_id:
            return jsonify({'signals': []})

        with signaling_lock:
            signals = incoming_signals.pop(device_id, [])

        return jsonify({'signals': signals})
    except Exception as e:
        logger.error(f"Get signals error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qr-code')
def get_qr_code():
    """Generate QR code for device pairing (no file transfer QR needed in P2P mode)"""
    try:
        # Use the current host URL (works for both local and hosted environments)
        device_id = session.get('device_id', 'unknown')
        base_url = request.host_url.rstrip('/')
        
        # Force HTTPS for public URLs (Render/etc) for WebRTC security
        if 'localhost' not in base_url and '127.0.0.1' not in base_url:
            base_url = base_url.replace('http://', 'https://')
            
        qr_data = f"{base_url}?pair={device_id}"
        logger.info(f"Generating pairing QR code for: {qr_data}")

        img = generate_qr_code(qr_data)
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        logger.error(f"QR code generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-peer-by-code/<code>', methods=['GET'])
def get_peer_by_code(code):
    """Get peer info by 6-digit pairing code"""
    try:
        with peers_lock:
            if code not in pairing_codes:
                return jsonify({'error': 'Invalid pairing code'}), 404

            device_id = pairing_codes[code]
            peer_info = peers.get(device_id)

            if not peer_info:
                return jsonify({'error': 'Peer not found'}), 404

            return jsonify({
                'device_id': device_id,
                'device_name': peer_info['device_name'],
                'pairing_code': code
            })

    except Exception as e:
        logger.error(f"Error getting peer by code: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    with peers_lock:
        active_peers = len(peers)

    return jsonify({
        'status': 'healthy',
        'active_peers': active_peers,
        'timestamp': datetime.now().isoformat()
    })

# Socket.IO Events for CLOUD MODE
@socketio.on('join')
def on_join(data):
    room = data.get('code')
    device_id = data.get('deviceId')
    role = data.get('role', 'receiver') # Default to receiver
    
    if room:
        join_room(room)
        if room not in rooms:
            rooms[room] = {'sender_sid': None, 'receiver_sid': None, 'created_at': time.time()}
        
        if role == 'sender':
            rooms[room]['sender_sid'] = request.sid
        else:
            rooms[room]['receiver_sid'] = request.sid
            if rooms[room]['sender_sid']:
                emit('peer_joined', {'room': room, 'peerId': device_id, 'role': 'receiver'}, to=rooms[room]['sender_sid'])
        
        logger.info(f"Socket: {role.upper()} {device_id} joined room {room}")
        emit('joined', {'role': role}, room=request.sid)

@socketio.on('offer')
def on_offer(data):
    room = data.get('code')
    if room:
        logger.info(f"Socket: [OFFER] From {data.get('from')} in room {room}")
        emit('offer', data, to=room, include_self=False)

@socketio.on('answer')
def on_answer(data):
    room = data.get('code')
    if room:
        logger.info(f"Socket: [ANSWER] From {data.get('from')} in room {room}")
        emit('answer', data, to=room, include_self=False)

@socketio.on('ice')
def on_ice(data):
    room = data.get('code')
    if room:
        emit('ice', data, to=room, include_self=False)

# ─── RELAY FALLBACK EVENTS ───

@socketio.on('relay-chunk-start')
def on_relay_start(data):
    room = data.get('code')
    if room in rooms and rooms[room]['receiver_sid']:
        emit('relay-chunk-start', data, to=rooms[room]['receiver_sid'])

@socketio.on('relay-chunk')
def on_relay_chunk(data):
    room = data.get('code')
    if room in rooms and rooms[room]['receiver_sid']:
        emit('relay-chunk', data, to=rooms[room]['receiver_sid'])

@socketio.on('relay-chunk-end')
def on_relay_end(data):
    room = data.get('code')
    if room in rooms and rooms[room]['receiver_sid']:
        emit('relay-chunk-end', data, to=rooms[room]['receiver_sid'])

@socketio.on('relay-ack')
def on_relay_ack(data):
    room = data.get('code')
    if room in rooms and rooms[room]['sender_sid']:
        emit('relay-ack', data, to=rooms[room]['sender_sid'])

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"  SWIFT — Secure Wireless Instant File Transfer")
    print(f"  Access at: http://{local_ip}:5000")
    print(f"  (Signaling Server for P2P communication)")
    print(f"{'='*50}\n")
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
