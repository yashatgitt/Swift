# SWIFT — P2P WebRTC File Transfer

A peer-to-peer file transfer application using WebRTC for direct device-to-device communication. Transfer large files instantly over local networks without storing files on a server.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

🚀 **Core Features:**
- **P2P Direct Transfer** — Files transfer directly between devices via WebRTC (no server storage)
- **Zero Configuration** — QR code & 6-digit code pairing for instant setup
- **Real-time Discovery** — Automatically discover peers on your network
- **Multiple Transfers** — Queue multiple files and transfer simultaneously
- **Cross-Platform** — Works on Windows, macOS, Linux, mobile browsers
- **Session Persistence** — Device ID persists across page refreshes
- **ICE Trickle-less** — Baked-in ICE candidates for reliable NAT traversal
- **Beautiful UI** — Dark/light theme toggle, responsive design

## How It Works

1. **Peer Discovery**: Devices register with a signaling server and discover other peers
2. **Manual Pairing**: Share a 6-digit code or QR code to pair devices
3. **WebRTC Connection**: Direct P2P connection established via ICE candidates
4. **File Transfer**: Files transfer directly peer-to-peer, bypassing the server

```
Device A                    Signaling Server              Device B
  |                              |                           |
  |------ Register peer -------->|                           |
  |                              |<------ Register peer --------|
  |------ Discover peers ------->|                           |
  |<----- Peer list -------------|                           |
  |                              |                           |
  |------------- WebRTC SDP Offer ---------->|
  |<------------- WebRTC SDP Answer ----------|
  |                          ===== P2P Connection =====
  |========== File transfer (direct) =========|
```

## Requirements

- **Python 3.7+**
- **Flask 3.0.0** — Web framework & signaling server
- **qrcode 7.4.2** — QR code generation
- **Pillow 10.1.0** — Image processing

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/swift-p2p.git
cd swift-p2p
```

### 2. Create a virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Running

### Start the signaling server
```bash
python app.py
```

The server will display:
```
==================================================
  P2P File Share Server
  Access at: http://192.168.x.x:5000
  (Server for signaling only - files transfer P2P)
==================================================
```

### Access from devices
- **Same network**: Open `http://<your-computer-ip>:5000` in any browser
- **From QR code**: Go to **Pairing** tab and scan the QR code
- **Manual pairing**: Enter the 6-digit pairing code from the **Pairing** tab

## Usage Guide

### 📡 Discover Tab
- View all available peers on your network
- Click **CONNECT** on any peer to initiate P2P connection
- Connection status shown in header

### 📤 Transfer Tab
- **Drop files** or click to select multiple files
- Monitor upload/download progress in real-time
- **Cancel** button to abort ongoing transfers
- **Session History** shows completed transfers (auto-cleared after 5 minutes)

### 🔗 Pairing Tab
- **QR Code**: Share with another device to auto-pair
- **6-Digit Code**: Manual code for pairing
- **Copy Link**: Generate shareable link with your device ID

## Architecture

### Frontend (p2p.html)
- **WebRTC**: Direct peer connection via RTCPeerConnection
- **DataChannel**: File chunks sent over encrypted data channel
- **LocalStorage**: Persists device ID across sessions
- **Responsive UI**: Works on desktop, tablet, mobile

### Backend (app.py)
- **Signaling Server**: Relays SDP offers/answers between peers
- **Peer Registry**: In-memory peer discovery (auto-cleanup after 5 minutes)
- **Pairing Codes**: 6-digit codes mapped to device IDs
- **ICE Candidates**: Baked into offer/answer (trickle-less)

## Configuration

### Environment Variables
```bash
# Change the secret key for production
export SECRET_KEY="your-secure-random-key"

# Run with custom port
python app.py  # Default: 5000
```

### Server Port
To run on a different port, modify `app.py`:
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main UI |
| `/api/device-info` | GET | Get current device ID |
| `/api/register-peer` | POST | Register peer for discovery |
| `/api/peers` | GET | Get list of available peers |
| `/api/signal` | POST | Exchange WebRTC SDP |
| `/api/incoming-signals` | GET | Poll for incoming offers/answers |
| `/api/qr-code` | GET | Generate QR code image |
| `/api/get-peer-by-code/<code>` | GET | Lookup peer by pairing code |

## Security Considerations

⚠️ **This is a local network app:**
- Only use on trusted networks
- All peers on the network can discover each other
- Signaling server does NOT store files (P2P only)
- Session tokens are browser-stored in localStorage
- Change `SECRET_KEY` in production

### For Internet Use
- Deploy behind a firewall
- Use HTTPS/WSS for signaling
- Implement authentication
- Consider rate limiting
- Use TURN servers for NAT traversal

## Troubleshooting

### Can't see other peers?
- Ensure all devices are on the same WiFi network
- Check firewall isn't blocking port 5000
- Wait 5+ seconds for peer discovery
- Try manual 6-digit code pairing

### Connection fails?
- Check browser console for WebRTC errors (F12)
- Verify signaling server is running
- If behind NAT, ensure TURN server configured (see TURN_SETUP.md)
- Try from a device directly on network (not VPN)

### Files won't transfer?
- Check DataChannel status in console logs
- Verify file size (tested up to 500MB)
- Ensure sufficient bandwidth
- Try smaller file first to diagnose

### Device ID not persisting?
- Check browser localStorage is enabled
- Try clearing browser cache and reload
- Device ID auto-generates if localStorage fails

## Performance

- **File Size**: Tested up to 500MB+ (limited by RAM/bandwidth)
- **Chunk Size**: 64KB per transfer (configurable in code)
- **Bandwidth**: Direct P2P, no server bottleneck
- **Latency**: Milliseconds (direct connection)

## Browser Support

| Browser | Desktop | Mobile |
|---------|---------|--------|
| Chrome | ✅ | ✅ |
| Firefox | ✅ | ✅ |
| Safari | ✅ | ⚠️ (iOS 11+) |
| Edge | ✅ | N/A |

## File Structure

```
swift-p2p/
├── app.py                    # Flask signaling server
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
├── templates/
│   └── p2p.html             # Frontend UI & WebRTC logic
├── run.sh / run.bat         # Convenience run scripts
├── TURN_SETUP.md            # NAT traversal configuration
├── MIGRATION_GUIDE.md       # Update notes
└── README_P2P.md            # Additional P2P documentation
```

## Recent Updates

### v1.0.0
- ✅ WebRTC ICE gathering wait (don't send offer before ICE complete)
- ✅ Session persistence via localStorage
- ✅ Trickle-less ICE (baked-in candidates)
- ✅ Peer auto-cleanup (5 minute expiration)
- ✅ Transfer UI: Auto-remove completed progress bars
- ✅ Device ID reuse on page refresh
- ✅ Fixed connection state logging

## Contributing

Found a bug? Want a feature?
1. Test on multiple devices/browsers
2. Include steps to reproduce
3. Share browser console errors
4. Submit via Issues

## License

MIT License — Free for personal and educational use

## Support

- 📖 Read TURN_SETUP.md for NAT traversal help
- 🔗 Check MIGRATION_GUIDE.md for version updates
- 🐛 Report bugs with browser console errors (F12)

---

**Made with ❤️ for peer-to-peer file sharing**
