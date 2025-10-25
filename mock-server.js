// mock-server.js — full working Express mock backend for QShield demo

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

// ===== Basic server setup =====
const app = express();
app.use(cors());
app.use(bodyParser.json());

function now() {
  return Math.floor(Date.now() / 1000);
}

// Generate encrypted-looking string for demo purposes
function generateEncryptedString(originalMessage) {
  // Create a base64-like encrypted appearance
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let encrypted = '';
  for (let i = 0; i < 32; i++) {
    encrypted += chars[Math.floor(Math.random() * chars.length)];
  }
  return encrypted;
}

// ====== In-memory stores ======
let messages = {}; // token -> message object
let approvals = {}; // request_id -> approval state
let demoKeys = {}; // recipientId -> keypair set

// ====== Routes ======

/**
 * Health check endpoint
 * GET /health
 */
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: now(),
    message: 'QShield Mock Server is running'
  });
});

/**
 * Admin: register demo keys for a recipient
 * POST /admin/register_demo_keys
 */
app.post('/admin/register_demo_keys', (req, res) => {
  const { recipientId, kyber_pub_b64, kyber_priv_b64, x25519_pub_b64, x25519_priv_b64 } = req.body;
  if (!recipientId || !kyber_pub_b64) {
    return res.status(400).json({ error: 'recipientId and kyber_pub_b64 required' });
  }
  demoKeys[recipientId] = {
    kyber_pub_b64,
    kyber_priv_b64: kyber_priv_b64 || null,
    x25519_pub_b64: x25519_pub_b64 || null,
    x25519_priv_b64: x25519_priv_b64 || null,
  };
  console.log('✅ Registered demo keys for', recipientId);
  return res.json({ status: 'ok', storedFor: recipientId });
});

/**
 * GET /pubkey/:id
 * Returns public keys for a recipient
 */
app.get('/pubkey/:id', (req, res) => {
  const id = req.params.id;
  const rec = demoKeys[id];
  if (!rec) return res.status(404).json({ error: 'no_keys' });
  return res.json({
    kyber_pub_b64: rec.kyber_pub_b64,
    x25519_pub_b64: rec.x25519_pub_b64 || null,
  });
});

/**
 * Demo-only: GET /me/privkey-demo?id=<recipientId>
 */
app.get('/me/privkey-demo', (req, res) => {
  const id = req.query.id;
  if (!id) return res.status(400).json({ error: 'id query param required' });
  const rec = demoKeys[id];
  if (!rec) return res.status(404).json({ error: 'no_keys' });
  return res.json({
    private_key_b64: rec.kyber_priv_b64 || null,
    x25519_private_b64: rec.x25519_priv_b64 || null,
  });
});

/**
 * POST /send — store ciphertext
 */
app.post('/send', (req, res) => {
  const { token, recipient_id, ciphertext_b64, nonce_b64, sender_eph_pub_b64, kem_ciphertext_b64, ttl_seconds, metadata } = req.body;
  if (!token || !recipient_id || !ciphertext_b64 || !kem_ciphertext_b64) {
    return res.status(400).json({ error: 'missing_fields' });
  }

  const force = metadata && metadata.force_policy;
  let policy = force || 'allow';
  const risk = Math.floor(Math.random() * 100);

  if (policy === 'pending_approval') {
    const request_id = 'req_' + Math.random().toString(36).slice(2, 9);
    approvals[request_id] = { status: 'pending' };
    messages[token] = { recipient_id, ciphertext_b64, nonce_b64, sender_eph_pub_b64, kem_ciphertext_b64, expiry: now() + (ttl_seconds || 90), createdAt: now(), state: 'pending', request_id };
    return res.json({ status: 'queued', risk, policy, message: 'Pending approval', request_id });
  } else if (policy === 'require_reauth') {
    messages[token] = { recipient_id, ciphertext_b64, nonce_b64, sender_eph_pub_b64, kem_ciphertext_b64, expiry: now() + (ttl_seconds || 90), createdAt: now(), state: 'require_reauth' };
    return res.json({ status: 'require_reauth', risk, policy, message: 'Require reauth' });
  } else if (policy === 'block') {
    return res.status(403).json({ status: 'blocked', risk, policy, message: 'Blocked by policy' });
  }

  // Default: allow
  // Store encrypted data with original message for demo purposes
  const originalMessage = req.body.original_message || 'Hello Bob! This is a secure message from Alice.';
  
  // Store encrypted data with original message for demo
  messages[token] = { 
    recipient_id, 
    ciphertext_b64, 
    nonce_b64, 
    sender_eph_pub_b64, 
    kem_ciphertext_b64, 
    original_message: originalMessage, // Store for demo decryption
    expiry: now() + (ttl_seconds || 90), // 90 seconds default
    createdAt: now(), 
    state: 'stored' 
  };
  return res.json({ status: 'stored', risk, policy, message: `Stored; will expire in ${ttl_seconds || 90}s` });
});

/**
 * GET /fetch/:token
 */
app.get('/fetch/:token', (req, res) => {
  const token = req.params.token;
  console.log(`🔍 Fetching message with token: ${token}`);
  const rec = messages[token];
  if (!rec) {
    console.log(`❌ No message found for token: ${token}`);
    return res.status(404).json({ detail: 'No message' });
  }
  if (rec.state !== 'stored') {
    console.log(`❌ Message not available, state: ${rec.state}`);
    return res.status(404).json({ detail: 'Not available' });
  }
  const ttl_remaining = Math.max(0, rec.expiry - now());
  console.log(`⏰ TTL remaining: ${ttl_remaining} seconds`);
  if (ttl_remaining <= 0) { 
    console.log(`❌ Message expired, deleting...`);
    delete messages[token]; 
    return res.status(404).json({ detail: 'Expired' }); 
  }
  
  console.log(`✅ Message found, returning encrypted data`);
  // Don't delete the message on fetch - only on explicit read
  return res.json({
    ciphertext_b64: rec.ciphertext_b64,
    nonce_b64: rec.nonce_b64,
    sender_eph_pub_b64: rec.sender_eph_pub_b64,
    kem_ciphertext_b64: rec.kem_ciphertext_b64,
    ttl_remaining,
    recipient_id: rec.recipient_id
  });
});

/**
 * POST /read/:token
 */
app.post('/read/:token', (req, res) => {
  const token = req.params.token;
  if (messages[token]) {
    delete messages[token];
    return res.json({ status: 'deleted' });
  }
  return res.status(404).json({ detail: 'No message' });
});

/**
 * GET /messages/:userId - Get all messages for a specific user
 */
app.get('/messages/:userId', (req, res) => {
  const userId = req.params.userId;
  console.log(`📨 Fetching messages for ${userId}...`);
  
  // Find all messages for this user
  const userMessages = [];
  for (const [token, message] of Object.entries(messages)) {
    if (message.recipient_id === userId) {
      // Check if message is still valid (not expired)
      const ttl_remaining = Math.max(0, message.expiry - now());
      if (ttl_remaining > 0) {
        userMessages.push({
          id: token,
          token: token,
          recipient_id: message.recipient_id,
          sender: 'Alice', // For demo, we know Alice is the sender
          content: `[ENCRYPTED] ${message.ciphertext_b64.substring(0, 32)}`, // Show consistent encrypted content (first 32 chars of actual ciphertext)
          original_content: message.original_message, // Include original for demo decryption
          timestamp: message.createdAt * 1000, // Convert to milliseconds
          ttl_remaining: ttl_remaining,
          state: message.state,
          decrypted: false // Mark as not yet decrypted
        });
      } else {
        // Message expired, remove it
        delete messages[token];
      }
    }
  }
  
  console.log(`📨 Found ${userMessages.length} messages for ${userId}`);
  res.json(userMessages);
});

/**
 * GET /pubkey/:userId - Get public keys for a specific user
 */
app.get('/pubkey/:userId', (req, res) => {
  const userId = req.params.userId;
  console.log(`🔑 Fetching keys for ${userId}...`);
  
  const userKeys = demoKeys[userId];
  if (!userKeys) {
    console.log(`❌ No keys found for ${userId}`);
    return res.status(404).json({ 
      error: 'User not found',
      message: `No keys registered for ${userId}` 
    });
  }
  
  console.log(`✅ Found keys for ${userId}`);
  res.json({
    recipientId: userId,
    kyber_pub_b64: userKeys.kyber_pub_b64,
    kyber_priv_b64: userKeys.kyber_priv_b64, // Include private key for decryption
    x25519_pub_b64: userKeys.x25519_pub_b64,
    x25519_priv_b64: userKeys.x25519_priv_b64, // Include private key for decryption
    registered: true
  });
});

// ===== Start server =====
const PORT = 8000;
app.listen(PORT, () => console.log(`🚀 Mock server running on http://localhost:${PORT}`));
