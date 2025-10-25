// Test script to verify encrypted message storage
const http = require('http');

// Test sending a message
const sendMessage = () => {
  const postData = JSON.stringify({
    token: 'test_token_123',
    recipient_id: 'bob',
    ciphertext_b64: 'encrypted_data_here',
    nonce_b64: 'nonce_here',
    sender_eph_pub_b64: 'eph_pub_here',
    kem_ciphertext_b64: 'kem_cipher_here',
    original_message: 'This is a test message from Alice',
    ttl_seconds: 15
  });

  const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/send',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };

  const req = http.request(options, (res) => {
    console.log(`Send Status: ${res.statusCode}`);
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
      console.log('Send Response:', data);
      // Now test fetching messages
      fetchMessages();
    });
  });

  req.write(postData);
  req.end();
};

// Test fetching messages
const fetchMessages = () => {
  const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/messages/bob',
    method: 'GET'
  };

  const req = http.request(options, (res) => {
    console.log(`Fetch Status: ${res.statusCode}`);
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
      console.log('Fetch Response:', data);
      try {
        const parsed = JSON.parse(data);
        if (parsed.length > 0) {
          console.log('Message content:', parsed[0].content);
          console.log('Original content:', parsed[0].original_content);
          console.log('Is encrypted format:', parsed[0].content.startsWith('[ENCRYPTED]'));
        }
      } catch (e) {
        console.log('Error parsing response:', e.message);
      }
    });
  });

  req.end();
};

// Start the test
console.log('Testing encrypted message storage...');
sendMessage();
