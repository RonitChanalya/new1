// Simple test to check if server is running with updated code
const http = require('http');

const options = {
  hostname: 'localhost',
  port: 8000,
  path: '/messages/bob',
  method: 'GET'
};

const req = http.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('Response:', data);
    try {
      const parsed = JSON.parse(data);
      if (parsed.length > 0) {
        console.log('Message content:', parsed[0].content);
        console.log('Has original_message field:', parsed[0].hasOwnProperty('original_message'));
      }
    } catch (e) {
      console.log('Error parsing response:', e.message);
    }
  });
});

req.on('error', (e) => {
  console.log('Request error:', e.message);
});

req.end();
