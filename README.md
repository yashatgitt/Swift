<div align="center">

<img src="swift_p2p_logo.png" width="150" height="150" alt="Swift Logo">

# 🚀 SWIFT — Secure Wireless Instant File Transfer

**Experience the future of local and remote file sharing. Fast, Private, and Peer-to-Peer.**

[![Version](https://img.shields.io/badge/version-1.0.0-blueviolet?style=for-the-badge)](https://github.com/yashatgitt/Swift)
[![Python](https://img.shields.io/badge/python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![WebRTC](https://img.shields.io/badge/webrtc-p2p-FF6F00?style=for-the-badge&logo=webrtc&logoColor=white)](https://webrtc.org/)
[![License](https://img.shields.io/badge/license-MIT-4CAF50?style=for-the-badge)](LICENSE)

[Features](#-features) • [How it Works](#-how-it-works) • [Installation](#-installation) • [Usage](#-usage-guide) • [Security](#-security) • [Troubleshooting](#-troubleshooting)

</div>

---

## 📱 The Swift Experience

Swift (**Secure Wireless Instant File Transfer**) is a high-performance, peer-to-peer file transfer application that leverages **WebRTC** to create a direct data pipeline between your devices. No more uploading to slow servers or worrying about cloud privacy.

<div align="center">
  <img src="swift_p2p_mockup.png" width="800" alt="Swift UI Mockup">
</div>

## ✨ Features

### 🛠️ Core Capabilities
*   **⚡ Blazing Fast P2P**: Direct device-to-device transfers using WebRTC Data Channels. No server bandwidth limits.
*   **🔒 Privacy First**: Files transfer directly. The signaling server only helps devices "find" each other; it never sees your data.
*   **🔗 Instant Pairing**: Seamlessly connect devices using a **6-digit pairing code** or a **QR code**.
*   **🌐 Universal Compatibility**: Works across Windows, macOS, Linux, Android, and iOS via any modern web browser.
*   **💾 No Installation Required**: For receivers, it's as simple as opening a URL or scanning a code.

### 🎨 Visual & UX Excellence
*   **🌓 Adaptive UI**: Beautiful dark and light modes that respect your system settings.
*   **📊 Real-time Tracking**: Monitor transfer speeds and progress with smooth animations.
*   **♻️ Session Persistence**: Your device identity stays the same even if you refresh the page.
*   **📱 Mobile Optimized**: Fully responsive design for a premium experience on phones and tablets.

---

## 🏗️ How It Works

Swift uses a "Signaling" architecture to establish a direct P2P link:

1.  **Discovery**: Both devices connect to the Swift signaling server.
2.  **Handshake**: Devices exchange encrypted metadata (SDP) and connection candidates (ICE).
3.  **Connection**: A direct, encrypted P2P tunnel is established.
4.  **Transfer**: Data flows directly through the tunnel at maximum network speed.

```mermaid
sequenceDiagram
    participant Peer A
    participant Signaling Server
    participant Peer B
    
    Peer A->>Signaling Server: Register & Get Pairing Code
    Peer B->>Signaling Server: Enter Code (Join Session)
    Signaling Server->>Peer A: Peer B is ready
    
    Peer A->>Signaling Server: Send WebRTC Offer
    Signaling Server->>Peer B: Relay Offer
    Peer B->>Signaling Server: Send WebRTC Answer
    Signaling Server->>Peer A: Relay Answer
    
    Note over Peer A, Peer B: Direct P2P Channel Established
    
    Peer A->>Peer B: 📁 High-Speed File Transfer (Direct)
```

---

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- `pip` (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/yashatgitt/Swift.git
cd Swift
```

### 2. Setup Environment
We recommend using a virtual environment to keep your dependencies clean:
```bash
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🛠️ Usage Guide

### Starting the Server
Run the signaling server on your host machine:
```bash
python app.py
```
The server will start at `http://localhost:5000` (and your local IP address).

### Connecting Devices
1.  **Open Swift** on the source device.
2.  Go to the **Pairing** tab to see your **6-digit code** or **QR code**.
3.  On the target device, enter the code or scan the QR.
4.  Once connected, go to the **Transfer** tab and drop your files!

---

## 🛡️ Security & Privacy

Swift is designed with a **privacy-first** mindset.

| Feature | Swift Implementation |
| :--- | :--- |
| **Data Storage** | **None.** Files are never stored on any server. |
| **Encryption** | WebRTC uses mandatory **DTLS/SRTP** encryption for all data. |
| **Server Role** | Only facilitates the initial handshake (signaling). |
| **Network** | Optimized for Local Area Networks (LAN), works via TURN for remote. |

> [!IMPORTANT]
> While Swift is encrypted, it is designed for use on trusted networks. For public internet use, ensure your signaling server is behind HTTPS.

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session security key | `default-secret-key` |
| `PORT` | The port the server runs on | `5000` |

---

## 🛠️ Troubleshooting

- **Peers not appearing?** Ensure both devices are on the same WiFi network and your computer's firewall allows incoming connections on port 5000.
- **Connection failing?** Some corporate/university networks block P2P traffic. Try using a mobile hotspot.
- **Large files slow?** Transfer speed is limited only by your local WiFi/Ethernet bandwidth. Use 5GHz WiFi for best results.

---

<div align="center">

### Built with ❤️ using Python, Flask, and WebRTC.

[Report a Bug](https://github.com/yashatgitt/Swift/issues) • [Request a Feature](https://github.com/yashatgitt/Swift/issues) • [Contribute](https://github.com/yashatgitt/Swift/pulls)

</div>
