# QShield - Post-Quantum Secure Messaging Demo

A secure messaging app demonstrating post-quantum cryptography with hybrid encryption (Kyber KEM + X25519 ECDH).

## 🛡️ Features

- **Post-Quantum Resistance**: Uses Kyber KEM for quantum-safe key encapsulation
- **Forward Secrecy**: Ephemeral keys for each message
- **Self-Destructing Messages**: TTL-based message deletion
- **Hybrid Encryption**: Combines post-quantum (Kyber) and classical (X25519) cryptography
- **Client-Side Encryption**: All crypto operations happen on the frontend

## 🏗️ Architecture

### Frontend (Expo React Native)
- **UI**: Chat interface with message bubbles and TTL countdown
- **Crypto**: Hybrid encryption using Kyber + X25519
- **Key Management**: Ephemeral key generation per message

### Backend (Mock Server)
- **Storage**: In-memory message storage
- **Key Registration**: Demo key management
- **TTL Management**: Automatic message expiration

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend/QShield
   npm install
   ```

2. **Start the mock server:**
   ```bash
   node mock-server.js
   ```
   Server runs on `http://localhost:8000`

3. **Start the Expo app:**
   ```bash
   npx expo start
   ```

4. **Open in browser:**
   - Click "Open in web browser" in Expo Dev Tools
   - Or scan QR code with Expo Go app

## 🧪 Demo Flow (60 seconds)

1. **Start server + Expo web**
2. **Register demo keys** - Click "Gen & Register alice"
3. **Send encrypted message** - Type a message and click "Send"
4. **Fetch → decrypt → message deleted** - Click "Fetch" on the message

## 🔐 Cryptographic Implementation

### Key Generation
- **Kyber KEM**: Post-quantum key encapsulation using `@openpgp/crystals-kyber-js`
- **X25519 ECDH**: Classical elliptic curve key exchange using `tweetnacl`

### Encryption Flow
1. Generate ephemeral X25519 keypair
2. Fetch recipient's Kyber public key
3. Kyber encapsulate to derive shared secret
4. Derive symmetric key using HKDF-like hash
5. Encrypt plaintext with XChaCha20-Poly1305
6. Send to server with TTL

### Decryption Flow
1. Fetch ciphertext from server
2. Kyber decapsulate with recipient private key
3. Derive symmetric key (Kyber + ECDH shared)
4. AEAD decrypt to get plaintext
5. Delete message from server

## 📁 Project Structure

```
frontend/QShield/
├── app/
│   ├── chat.tsx              # Main chat interface
│   └── components/
│       └── MessageBubble.tsx # Message display component
├── src/
│   ├── services/
│   │   ├── cryptoService.ts  # Hybrid encryption logic
│   │   └── messageService.ts # Message handling
│   ├── utils/
│   │   └── base64.ts        # Base64 utilities
│   └── api.ts               # API client
├── mock-server.js           # Mock backend server
└── package.json
```

## 🔧 API Endpoints

### Mock Server Endpoints
- `POST /admin/register_demo_keys` - Register demo keys
- `GET /pubkey/:id` - Get recipient public keys
- `POST /send` - Store encrypted message
- `GET /fetch/:token` - Retrieve message
- `POST /read/:token` - Delete message after reading

## 🧪 Testing

1. **Register demo keys** ✅
2. **Send message → `/send`** ✅
3. **Fetch & decrypt → `/fetch/:token`** ✅
4. **Verify deletion → `404`** ✅

## 🛠️ Technologies Used

- **Frontend**: Expo React Native, TypeScript
- **Crypto**: `@openpgp/crystals-kyber-js`, `tweetnacl`, `libsodium-wrappers`
- **Backend**: Node.js, Express
- **Utilities**: `uuid`, `axios`

## 📝 Notes

- This is a **demo/prototype** for educational purposes
- The mock server stores private keys for demo convenience (not production-ready)
- All cryptographic operations are performed client-side
- Messages are automatically deleted after reading or TTL expiry

## 🎯 Security Features

- **Post-Quantum Resistance**: Kyber KEM protects against future quantum attacks
- **Forward Secrecy**: Each message uses new ephemeral keys
- **Self-Destructing**: Messages automatically expire
- **Hybrid Security**: Combines post-quantum and classical cryptography
- **Client-Side Encryption**: Server never sees plaintext

## 🚀 Future Enhancements

- Real backend with proper key management
- User authentication and authorization
- Group messaging support
- Message threading
- File sharing with encryption
- Mobile app deployment