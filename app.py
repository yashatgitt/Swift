import os
import socket
import qrcode
import base64
import random
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify, session
from datetime import datetime
import uuid
import logging
import time
from threading import Lock

app = Flask(__name__)
# Generate a secure random key if not provided
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/api/signal', methods=['POST'])
def webrtc_signal():
    """WebRTC signaling - exchange SDP offers and answers"""
    try:
        data = request.json
        from_device = session.get('device_id')
        to_device = data.get('to_device')
        signal_type = data.get('type')  # 'offer' or 'answer'
        sdp = data.get('sdp')

        # Store both directions for easier lookup
        connection_id_ab = f"{from_device}-{to_device}"
        connection_id_ba = f"{to_device}-{from_device}"

        logger.info(f"WebRTC signaling: {signal_type} from {from_device} to {to_device}")

        with signaling_lock:
            # Initialize both directions if needed
            if connection_id_ab not in signaling_data:
                signaling_data[connection_id_ab] = {
                    'offer': None,
                    'answer': None,
                    'candidates_a': [],
                    'candidates_b': [],
                    'from_device': from_device,
                    'to_device': to_device
                }

            if connection_id_ba not in signaling_data:
                signaling_data[connection_id_ba] = {
                    'offer': None,
                    'answer': None,
                    'candidates_a': [],
                    'candidates_b': [],
                    'from_device': to_device,
                    'to_device': from_device
                }

            # Store the signal
            if signal_type == 'offer':
                # Reset old connection data when a new offer starts
                signaling_data[connection_id_ab].update({
                    'offer': sdp,
                    'answer': None,
                    'candidates_a': [],
                    'candidates_b': [],
                    'timestamp': time.time()
                })
                signaling_data[connection_id_ba].update({
                    'offer': sdp,
                    'answer': None,
                    'candidates_a': [],
                    'candidates_b': [],
                    'timestamp': time.time()
                })
                logger.info(f"New connection initiated: {connection_id_ab}")
            elif signal_type == 'answer':
                signaling_data[connection_id_ab]['answer'] = sdp
                signaling_data[connection_id_ba]['answer'] = sdp
                signaling_data[connection_id_ab]['timestamp'] = time.time()
                signaling_data[connection_id_ba]['timestamp'] = time.time()
                logger.info(f"Answer stored for {connection_id_ab}")

        return jsonify({'status': 'signaled', 'connection_id': connection_id_ab})

    except Exception as e:
        logger.error(f"Error in WebRTC signaling: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-offer/<to_device>', methods=['GET'])
def get_offer(to_device):
    """Get incoming offer from another device"""
    try:
        device_id = session.get('device_id')
        connection_id = f"{to_device}-{device_id}"

        logger.debug(f"Device {device_id} checking for offer from {to_device}")

        with signaling_lock:
            if connection_id not in signaling_data:
                return jsonify({'status': 'no_offer'})

            signal_info = signaling_data[connection_id]

            if signal_info.get('offer'):
                return jsonify({
                    'type': 'offer',
                    'sdp': signal_info['offer'],
                    'from_device': to_device,
                    'candidates': signal_info.get('candidates_a', [])
                })

        return jsonify({'status': 'no_offer'})

    except Exception as e:
        logger.error(f"Error getting offer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-signal/<connection_id>', methods=['GET'])
def get_signal(connection_id):
    """Get stored signaling data (offer or answer) for a connection"""
    try:
        with signaling_lock:
            if connection_id not in signaling_data:
                return jsonify({'status': 'no_signal'}), 200

            signal_info = signaling_data[connection_id]
            response = {
                'connection_id': connection_id,
                'from_device': signal_info.get('from_device'),
                'to_device': signal_info.get('to_device')
            }

            if signal_info.get('offer'):
                response['type'] = 'offer'
                response['sdp'] = signal_info['offer']
                response['candidates'] = signal_info.get('candidates_a', [])

            if signal_info.get('answer'):
                response['type'] = 'answer'
                response['sdp'] = signal_info['answer']
                response['candidates'] = signal_info.get('candidates_b', [])

            if not signal_info.get('offer') and not signal_info.get('answer'):
                return jsonify({'status': 'waiting'}), 200

            return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting signal: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/incoming-signals', methods=['GET'])
def get_incoming_signals():
    """Get all incoming signals (offers, answers, candidates) for the current device"""
    try:
        device_id = session.get('device_id')
        if not device_id: return jsonify({'signals': []})
            
        incoming = []
        with signaling_lock:
            for cid, data in signaling_data.items():
                if data.get('to_device') == device_id:
                    # Signals where this device is the target
                    signal = {
                        'from_device': data.get('from_device'),
                        'offer': data.get('offer'),
                        'answer': data.get('answer'),
                        'candidates': data.get('candidates_a', []) if data.get('from_device') != device_id else data.get('candidates_b', [])
                    }
                    
                    if signal['offer'] or signal['answer'] or signal['candidates']:
                        incoming.append(signal)
                        # Clear signaling data after it's been consumed
                        data['offer'] = None
                        data['answer'] = None
                        data['candidates_a'] = []
                        data['candidates_b'] = []
                        
        return jsonify({'signals': incoming})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ice-candidate', methods=['POST'])
def ice_candidate():
    """Relay ICE candidates for NAT traversal"""
    try:
        data = request.json
        from_device = session.get('device_id')
        to_device = data.get('to_device')
        candidate = data.get('candidate')

        connection_id_ab = f"{from_device}-{to_device}"
        connection_id_ba = f"{to_device}-{from_device}"

        with signaling_lock:
            for cid in [connection_id_ab, connection_id_ba]:
                if cid not in signaling_data:
                    signaling_data[cid] = {
                        'offer': None,
                        'answer': None,
                        'candidates_a': [],
                        'candidates_b': [],
                        'from_device': from_device,
                        'to_device': to_device
                    }

                # Ensure candidates are added to the correct list based on the sender
                if from_device == signaling_data[cid].get('from_device'):
                    signaling_data[cid]['candidates_a'].append(candidate)
                else:
                    signaling_data[cid]['candidates_b'].append(candidate)

        logger.debug(f"ICE candidate relayed: {from_device} -> {to_device}")
        return jsonify({'status': 'relayed'})

    except Exception as e:
        logger.error(f"Error relaying ICE candidate: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qr-code')
def get_qr_code():
    """Generate QR code for device pairing (no file transfer QR needed in P2P mode)"""
    try:
        # Use the current host URL (works for both local and hosted environments)
        device_id = session.get('device_id', 'unknown')
        base_url = request.host_url.rstrip('/')
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

@app.route('/api/qr-code-data')
def get_qr_code_data():
    """Get QR code data as base64"""
    try:
        device_id = session.get('device_id', 'unknown')
        
        base_url = request.host_url.rstrip('/')
        qr_data = f"{base_url}?pair={device_id}"

        img = generate_qr_code(qr_data)
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.getvalue()).decode()

        return jsonify({
            'url': qr_data,
            'image': f'data:image/png;base64,{img_base64}',
            'device_id': device_id,
            'ip': local_ip,
            'port': port
        })
    except Exception as e:
        logger.error(f"QR code data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pair', methods=['POST'])
def pair_device():
    """Mark device as paired"""
    try:
        data = request.json or {}
        device_id = session.get('device_id', 'unknown')

        logger.info(f"Device paired: {device_id}")
        return jsonify({'status': 'paired', 'device_id': device_id})

    except Exception as e:
        logger.error(f"Error pairing: {e}")
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

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"  SWIFT — Secure Wireless Instant File Transfer")
    print(f"  Access at: http://{local_ip}:5000")
    print(f"  (Signaling Server for P2P communication)")
    print(f"{'='*50}\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
