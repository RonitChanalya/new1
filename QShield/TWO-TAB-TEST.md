# 🧪 Two-Tab Testing Guide

## **Setup Instructions:**

### **Step 1: Start the Mock Server**
```bash
cd BrainWar/frontend/QShield
node mock-server.js
```
You should see: `🚀 Mock server running on http://localhost:8000`

### **Step 2: Start the Expo App**
```bash
# In a new terminal
cd BrainWar/frontend/QShield
npx expo start --web
```
Open the URL in your browser (usually `http://localhost:8081`)

---

## **🎯 Two-Tab Testing Flow:**

### **Tab 1: Alice (Sender)**
1. **Register Alice:**
   - Click "Register Alice" button
   - Should see green success banner: "✅ alice registered successfully!"

2. **Send Message to Bob:**
   - Type a message: "Hello Bob from Alice!"
   - Click "Send to Bob" button
   - Should see message with "📤 Sending..." then "✅ Stored securely"

### **Tab 2: Bob (Receiver)**
1. **Open second browser tab** to the same Expo URL
2. **Register Bob:**
   - Click "Register Bob" button
   - Should see green success banner: "✅ bob registered successfully!"

3. **Fetch Bob's Messages:**
   - Click "Fetch Bob's Messages" button
   - Should see the message from Alice in the alert

4. **Decrypt and Read:**
   - The message should show "🔍 Fetch & Decrypt" button
   - Click it to decrypt and read the message

---

## **🔍 What to Look For:**

### **Success Indicators:**
- ✅ **Server Connected** status in both tabs
- ✅ **Registration success** banners
- ✅ **Message sending** with proper status updates
- ✅ **Message fetching** shows encrypted data
- ✅ **Decryption** reveals original message

### **Console Output:**
- **Registration:** "🎉 SUCCESS: [user] registered successfully!"
- **Sending:** "Trying instance encapsulate methods..."
- **Fetching:** API calls to `/messages/[user]`
- **Decryption:** "Successfully decapsulated using instance method"

---

## **🚨 Troubleshooting:**

### **If Registration Fails:**
- Check server is running: `🚀 Mock server running on http://localhost:8000`
- Check console for API errors
- Try refreshing the page

### **If Sending Fails:**
- Check "Kyber encapsulate API not found" error
- Look for "Trying instance encapsulate methods..." in console
- Verify both users are registered

### **If Fetching Fails:**
- Check "Fetch Bob's Messages" button works
- Verify message was sent successfully
- Check server logs for message storage

---

## **🎉 Expected Final Result:**

1. **Alice sends** encrypted message to Bob
2. **Bob receives** encrypted message data
3. **Bob decrypts** and reads the original message
4. **Both tabs show** proper status indicators

This demonstrates the complete **hybrid post-quantum cryptography** flow with **Kyber KEM + X25519 ECDH**!
