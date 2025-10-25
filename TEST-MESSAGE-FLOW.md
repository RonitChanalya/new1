# 🧪 Test Message Flow - Step by Step

## **🔧 Fixed Issues:**

1. **Added `/messages/{userId}` endpoint** to mock server
2. **Enhanced debugging** in frontend message fetching
3. **Proper message storage** and retrieval

## **🎯 Step-by-Step Test:**

### **Step 1: Start the Updated Server**
```bash
cd BrainWar/frontend/QShield
node mock-server.js
```
**Expected:** `🚀 Mock server running on http://localhost:8000`

### **Step 2: Start the Expo App**
```bash
npx expo start --web
```
**Expected:** Opens browser with QShield app

### **Step 3: Test Message Flow**

#### **Tab 1 (Alice - Sender):**
1. **Select Alice** (blue button should be highlighted)
2. **Register Alice** → Should see "✅ alice registered successfully!"
3. **Send to Bob**: Type "Hello Bob from Alice!" and click "Send to Bob"
4. **Watch AI**: Should see "🔍 Scanning..." → "🛡️ Secure"
5. **Check Status**: Message should show "📤 Sending..." → "✅ Stored securely"

#### **Tab 2 (Bob - Receiver):**
1. **Select Bob** (green button should be highlighted)
2. **Register Bob** → Should see "✅ bob registered successfully!"
3. **Fetch Bob's Messages** → Click "Fetch Bob's Messages"
4. **Check Console**: Should see detailed API logs
5. **Check Messages**: Should see Alice's message in green box

## **🔍 What to Look For:**

### **Server Logs:**
```
📨 Fetching messages for bob...
📨 Found 1 messages for bob
```

### **Frontend Console:**
```
🔍 Fetching messages for bob...
🔍 API call: GET /messages/bob
📨 API Response for bob: {status: 200, data: [...]}
✅ Found 1 messages for bob
```

### **UI Changes:**
- **Success Banner**: "📨 Found 1 messages for bob"
- **Received Messages**: Green box with Alice's message
- **Message Content**: "[ENCRYPTED]" (since it's encrypted)

## **🚨 Troubleshooting:**

### **If No Messages Appear:**
1. **Check Server Logs**: Look for "📨 Fetching messages for bob..."
2. **Check Console**: Look for API call logs
3. **Verify Registration**: Make sure both Alice and Bob are registered
4. **Check Timing**: Messages expire after 15 seconds

### **If API Call Fails:**
1. **Check Server**: Make sure server is running on port 8000
2. **Check Endpoint**: Verify `/messages/bob` endpoint exists
3. **Check CORS**: Make sure CORS is enabled
4. **Check Network**: Look for 404 or 500 errors

### **If Messages Are Empty:**
1. **Check Message Storage**: Look for "✅ Registered demo keys for alice/bob"
2. **Check Message Sending**: Look for "Stored; will expire in 15s"
3. **Check Message Fetching**: Look for "📨 Found X messages for bob"

## **🎯 Expected Results:**

1. **Alice sends** message to Bob
2. **Server stores** message with recipient_id = "bob"
3. **Bob fetches** messages using GET /messages/bob
4. **Server returns** Alice's message for Bob
5. **Frontend displays** message in green box (received message)

## **🔧 Debug Commands:**

### **Test Server Endpoint:**
```bash
curl http://localhost:8000/messages/bob
```

### **Check Server Health:**
```bash
curl http://localhost:8000/health
```

### **Check All Messages:**
```bash
curl http://localhost:8000/messages/alice
```

The message fetching should now work properly! 🎉
