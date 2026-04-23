# SWIFT

<div align="center">

**Secure Wireless Instant File Transfer**

[![Version](https://img.shields.io/badge/version-1.1.0-6366f1?style=flat-square)](https://github.com/yashatgitt/Swift)
[![Python](https://img.shields.io/badge/python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-2.x-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![WebRTC](https://img.shields.io/badge/WebRTC-P2P-ff4d00?style=flat-square)](https://webrtc.org)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.x-010101?style=flat-square&logo=socket.io)](https://socket.io)
[![License](https://img.shields.io/badge/license-MIT-00c896?style=flat-square)](LICENSE)
[![Maintained](https://img.shields.io/badge/maintained-yes-00c896?style=flat-square)]()

<br/>

> Browser-to-browser file transfer. No cloud. No account. No size limit.  
> Files go directly from your device to theirs — encrypted, instant, private.

<br/>

[**Live Demo**](https://swift.onrender.com) · [**Report Bug**](https://github.com/yashatgitt/Swift/issues) · [**Request Feature**](https://github.com/yashatgitt/Swift/issues)

</div>

---

## What is SWIFT?

Most file sharing tools work like this: you upload to a server, they download from a server. Your file touches someone else's disk, gets logged, gets scanned, and sits there until you delete it.

SWIFT doesn't do that.

SWIFT creates a direct encrypted tunnel between two browsers using WebRTC. The server is only involved for ~2 seconds during the initial handshake — after that it steps out completely. The file never leaves your device until it reaches the other person.

When a direct connection isn't possible (different networks, strict NAT), SWIFT automatically falls back to a Socket.IO relay. Either way, no file is ever stored on disk.

---

## Features

- **Zero storage** — files stream directly between browsers, nothing is written to disk
- **Local + Cloud modes** — LAN mode for same-network transfers, Cloud mode for cross-network via TURN/relay
- **LAN turbo** — detects same-network connections and boosts chunk size to 256KB automatically
- **Batch transfers** — select multiple files, preview them before sending, remove individual files from queue
- **Live telemetry** — real-time speed in MB/s, ETA countdown, per-file progress
- **6-digit pairing** — connect by code or QR scan, no accounts
- **Custom device names** — name your devices, stored in localStorage
- **Transfer history** — session log of sent and received files
- **Dark/light theme** — persists across sessions

---

## How It Works

### Connection Flow

```
Device A                    Flask Server                   Device B
   |                              |                              |
   |── POST /api/register-peer ──>|                              |
   |<── pairing_code: 482910 ────|                              |
   |                              |<── POST /api/register-peer ──|
   |                              |─── pairing_code: 731045 ───>|
   |                              |                              |
   |── enter code 731045 ────────>|                              |
   |<── device_id of B ──────────|                              |
   |                              |                              |
   |══════════ WebRTC Offer ══════════════════════════════════>|
   |<═════════ WebRTC Answer ════════════════════════════════════|
   |<═════════ ICE Candidates ═══════════════════════════════════|
   |                              |                              |
   |◄────────── Direct P2P DataChannel ──────────────────────►|
   |                   (server steps out)                        |
   |                                                             |
   |════════════════ File chunks (encrypted) ════════════════>|
```

### Path Selection Logic

```
Connection attempt
        │
        ▼
   Same network?
   ┌────┴────┐
  YES       NO
   │         │
   ▼         ▼
 Direct    STUN traversal
 LAN P2P   attempted
 256KB      │
 chunks    Succeeds? ──NO──► Socket.IO relay fallback
            │
           YES
            ▼
        Direct P2P
        64KB chunks
```

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Browser                          │
│                                                         │
│   ┌─────────────┐      ┌──────────────────────────┐    │
│   │   Swift UI  │      │     WebRTC Engine        │    │
│   │  (Vanilla   │◄────►│  RTCPeerConnection       │    │
│   │   JS/CSS)   │      │  RTCDataChannel          │    │
│   └──────┬──────┘      └────────────┬─────────────┘    │
│          │                          │                   │
└──────────┼──────────────────────────┼───────────────────┘
           │ HTTP polling             │ ICE candidates
           │ (LOCAL mode)             │ (both modes)
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Flask + Socket.IO                    │
│                                                         │
│   /api/register-peer    →  peer registry (in-memory)   │
│   /api/signal           →  SDP relay                   │
│   /api/get-signals      →  signal polling              │
│   socket: offer/answer  →  Socket.IO relay (CLOUD)     │
│   socket: ice           →  ICE candidate relay         │
│                                                         │
│   ⚠️  No file data ever passes through this server     │
└─────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Modern browser (Chrome, Firefox, Edge, Safari)

### Installation

```bash
git clone https://github.com/yashatgitt/Swift.git
cd Swift
```

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

```bash
python app.py
```

Open `http://localhost:5000` in two browser tabs or on two devices on the same network.

---

## Usage

### LOCAL Mode (Same Network)

1. Open Swift on both devices connected to the same WiFi
2. Go to **Discover** tab — your device appears automatically
3. Click **Connect** on the other device's card
4. Drop files and send

### CLOUD Mode (Different Networks)

1. Switch to **Cloud** mode using the toggle in the header
2. Share your 6-digit pairing code or QR with the other person
3. They enter the code on their end
4. Drop files and send

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS, CSS3, HTML5 |
| Backend | Python, Flask |
| Real-time | Socket.IO (Flask-SocketIO) |
| P2P | WebRTC DataChannel |
| NAT Traversal | STUN (Google Public) |
| QR | qrcode (Python) |
| Fonts | Space Grotesk, JetBrains Mono, DM Sans |

---

## Security

| Concern | How SWIFT handles it |
|---|---|
| Data in transit | DTLS encryption mandatory on all WebRTC DataChannels |
| Server storage | Zero — no file data is written anywhere |
| Signaling privacy | Pairing codes expire, signals cleared after use |
| Session isolation | Each device gets a unique session ID |
| Relay fallback | Socket.IO fallback is encrypted end-to-end |

---

## Project Structure

```
Swift/
├── app.py                  # Flask server, signaling, Socket.IO
├── requirements.txt
├── .env                    # Environment variables (not committed)
├── templates/
│   └── p2p.html            # Entire frontend — UI, WebRTC, transfer logic
└── temp_uploads/           # Never used in P2P mode (relay fallback only)
```

---

## Roadmap

- [x] Core WebRTC P2P transfer
- [x] 6-digit pairing code + QR
- [x] Cloud mode via Socket.IO Relay
- [x] LAN turbo mode (256KB chunks)
- [x] Batch file preview queue
- [x] Live speed + ETA telemetry
- [x] Custom device naming
- [x] Transfer history
- [ ] Folder transfer support
- [ ] Progressive Web App (PWA) — install on mobile
- [ ] Desktop app via PyInstaller zip (no Electron)
- [ ] Android app via React Native

---

## Author

Built by **Yash Gangurde** — IT Engineering Student, Pune  
GitHub: [@yashatgitt](https://github.com/yashatgitt)  
LinkedIn: [yash-gangurde](https://linkedin.com/in/yash-gangurde-95557328b)

---

<div align="center">

**SWIFT** — Fast. Private. Direct.

</div>
