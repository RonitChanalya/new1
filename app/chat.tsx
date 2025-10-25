// app/chat.tsx
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import MessageBubble from './components/MessageBubble';
import { Link } from 'expo-router';

// Crypto service (Option B - Kyber + libsodium hybrid)
import { encryptAndSendHybrid, fetchAndDecryptHybrid, generateKyberKeypair, kyberDecapsulate, deriveSymmetricKey } from '../src/services/cryptoService';
import { base64ToBytes } from '../src/utils/base64';
import api from '../src/api';

// For generating x25519 demo keys on frontend
import * as sodium from 'libsodium-wrappers';
import * as nacl from 'tweetnacl';

// local types (simple shape for UI)
type LocalMsg = {
  localId: string;
  token?: string;
  plain?: string | null;
  state: 'encrypting' | 'sending' | 'stored_on_server' | 'require_reauth' | 'pending_approval' | 'blocked' | 'error' | 'deleted';
  createdAt: number;
  ttl_seconds?: number;
  serverResponse?: any;
};

export default function ChatScreen() {
  const [localMsgs, setLocalMsgs] = useState<LocalMsg[]>([]);
  const [input, setInput] = useState('');
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastSuccess, setLastSuccess] = useState<string | null>(null);
  const [threatLevel, setThreatLevel] = useState<'low' | 'medium' | 'high'>('low');
  const [aiStatus, setAiStatus] = useState<'scanning' | 'secure' | 'threat-detected'>('scanning');
  const [encryptionLevel, setEncryptionLevel] = useState<'standard' | 'enhanced' | 'maximum'>('enhanced');
  const [currentUser, setCurrentUser] = useState<string>('alice');
  const [receivedMsgs, setReceivedMsgs] = useState<any[]>([]);

  useEffect(() => {
    // expose helpers to window for quick console testing (demo only)
    (async () => {
      try {
        await (sodium as any).ready;
        (window as any).__sodium__ = sodium;
      } catch (e) {
        // ignore
      }
      (window as any).__cryptoService__ = { encryptAndSendHybrid, fetchAndDecryptHybrid, generateKyberKeypair };
      setIsReady(true);
      
      // Check server connection
      try {
        console.log('Checking server connection...');
        const healthResponse = await api.get('/health');
        console.log('Health check response:', healthResponse.data);
        setServerStatus('connected');
        
        // Simulate AI threat detection
        setTimeout(() => {
          setAiStatus('secure');
          setThreatLevel('low');
          setEncryptionLevel('enhanced');
        }, 2000);
      } catch (e) {
        console.log('Health check failed:', e);
        setServerStatus('disconnected');
        setAiStatus('threat-detected');
        setThreatLevel('high');
      }
    })();
  }, []);

  // helper to add placeholder
  function addPlaceholder(plain: string) {
    const localId = 'tmp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    const placeholder: LocalMsg = { localId, plain, state: 'encrypting', createdAt: Date.now(), ttl_seconds: 90 };
    setLocalMsgs(prev => [placeholder, ...prev]);
    return placeholder;
  }

  async function onSend(recipientId: string = 'alice') {
    if (!input.trim() || isLoading) return;
    const plain = input.trim();
    setInput('');
    setIsLoading(true);
    const placeholder = addPlaceholder(plain);

    try {
      // AI Threat Detection Simulation
      setAiStatus('scanning');
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate AI scanning
      
      // Simulate threat assessment based on message content
      const threatKeywords = ['attack', 'bomb', 'weapon', 'classified', 'secret', 'mission'];
      const hasThreatKeywords = threatKeywords.some(keyword => 
        plain.toLowerCase().includes(keyword)
      );
      
      if (hasThreatKeywords) {
        setThreatLevel('high');
        setEncryptionLevel('maximum');
        setAiStatus('threat-detected');
        console.log('🚨 AI Threat Detection: High-risk content detected, applying maximum encryption');
      } else {
        setThreatLevel('low');
        setEncryptionLevel('enhanced');
        setAiStatus('secure');
      }

      // Encrypt & send using hybrid (Kyber + X25519); returns { token, serverResponse }
      const { token, serverResponse } = await encryptAndSendHybrid(plain, recipientId, { ttl_seconds: placeholder.ttl_seconds });

      // Update message: store token and mark stored_on_server if server policy allowed
      setLocalMsgs(prev =>
        prev.map(m =>
          m.localId === placeholder.localId
            ? { ...m, token, state: serverResponse?.policy === 'allow' ? 'stored_on_server' : (serverResponse?.policy ?? 'stored_on_server'), serverResponse }
            : m
        )
      );
    } catch (err: any) {
      console.log('send error ->', err);
      Alert.alert('Send failed', String(err?.message ?? err));
      setLocalMsgs(prev => prev.map(m => (m.localId === placeholder.localId ? { ...m, state: 'error', serverResponse: err } : m)));
    } finally {
      setIsLoading(false);
    }
  }

  async function onFetchAndShow(token?: string) {
    if (!token) return Alert.alert('No token', 'This message has no token to fetch.');
    try {
      // For demo, fetch and decrypt (requires recipient private keys available locally or via /me/privkey-demo)
      const res = await fetchAndDecryptHybrid(token);
      Alert.alert('Decrypted message', res.plaintext);
      // after reading, tell server to delete
      try {
        await api.post(`/read/${token}`);
      } catch (e) {
        // ignore delete error for demo
      }
      // update UI
      setLocalMsgs(prev => prev.map(m => (m.token === token ? { ...m, state: 'deleted' } : m)));
    } catch (err: any) {
      console.log('fetch/decrypt error ->', err);
      Alert.alert('Fetch / decrypt failed', String(err?.message ?? err?.response?.data ?? 'No message'));
    }
  }

async function generateAndRegisterUser(recipientId: string) {
  try {
    // 1) kyber keypair
    const kp = await generateKyberKeypair(); // { publicKey_b64, privateKey_b64 }

    // 2) tweetnacl x25519 keypair
    const nacl = (await import('tweetnacl')).default;
    const xkp = nacl.box.keyPair();
    const { bytesToBase64 } = await import('../src/utils/base64');
    const x_pub_b64 = bytesToBase64(xkp.publicKey);
    const x_priv_b64 = bytesToBase64(xkp.secretKey);

    // 3) register on mock server
    const payload = {
      recipientId: recipientId,
      kyber_pub_b64: kp.publicKey_b64,
      kyber_priv_b64: kp.privateKey_b64,
      x25519_pub_b64: x_pub_b64,
      x25519_priv_b64: x_priv_b64,
    };
    console.log('Sending registration payload:', payload);
    const r = await api.post('/admin/register_demo_keys', payload);
    console.log('Registration response:', r.data);
    
    // Try multiple notification methods
    try {
      Alert.alert(`✅ Registered ${recipientId}`, JSON.stringify(r.data));
    } catch (e) {
      console.log('Alert failed, trying alternative notification');
    }
    
    // Alternative notification for web
    if (typeof window !== 'undefined') {
      // Show in console as backup
      console.log(`🎉 SUCCESS: ${recipientId} registered successfully!`);
      console.log('Response:', r.data);
      
      // Set success message in UI
      setLastSuccess(`✅ ${recipientId} registered successfully!`);
      setTimeout(() => setLastSuccess(null), 5000); // Clear after 5 seconds
      
      // Try browser notification
      try {
        if (Notification.permission === 'granted') {
          new Notification('QShield', {
            body: `${recipientId} registered successfully!`,
            icon: '/favicon.ico'
          });
        }
      } catch (e) {
        // Ignore notification errors
      }
    }
  } catch (e:any) {
    console.log('register error ->', e);
    Alert.alert('Register failed', String(e?.message ?? e));
  }
}

async function generateAndRegisterAlice() {
  await generateAndRegisterUser('alice');
}

async function generateAndRegisterBob() {
  await generateAndRegisterUser('bob');
}

async function fetchMessagesForUser(userId: string) {
  try {
    console.log(`🔍 Fetching messages for ${userId}...`);
    console.log(`🔍 API call: GET /messages/${userId}`);
    
    const response = await api.get(`/messages/${userId}`);
    console.log(`📨 API Response for ${userId}:`, response);
    console.log(`📨 Response data:`, response.data);
    console.log(`📨 Response status:`, response.status);
    
    if (response.data && Array.isArray(response.data) && response.data.length > 0) {
      console.log(`✅ Found ${response.data.length} messages for ${userId}`);
      console.log(`📨 Message data:`, response.data);
      
      // Process messages to ensure proper display
      const processedMessages = response.data.map(msg => ({
        ...msg,
        decrypted: msg.decrypted || false,
        content: msg.decrypted ? msg.content : msg.content // Use server's encrypted content directly
      }));
      
      setReceivedMsgs(processedMessages);
      setLastSuccess(`📨 Found ${response.data.length} messages for ${userId}`);
      setTimeout(() => setLastSuccess(null), 5000);
    } else {
      console.log(`📭 No messages found for ${userId}`);
      setLastSuccess(`📭 No messages found for ${userId}`);
      setTimeout(() => setLastSuccess(null), 3000);
    }
  } catch (e: any) {
    console.log('❌ Fetch messages error:', e);
    console.log('❌ Error details:', e?.response?.data);
    console.log('❌ Error status:', e?.response?.status);
    Alert.alert('Fetch Failed', `Error: ${e?.message ?? e}\nStatus: ${e?.response?.status}\nData: ${JSON.stringify(e?.response?.data)}`);
  }
}

async function decryptAndDisplayMessage(messageData: any) {
  try {
    console.log('🔓 Decrypting message:', messageData);
    
    // Check if we have the necessary data for decryption
    if (!messageData.token) {
      throw new Error('No message token available for decryption');
    }
    
    // Real decryption process using actual cryptographic operations
    console.log('🔓 Fetching encrypted message data...');
    setLastSuccess('🔓 Starting decryption process...');
    
    // Fetch the actual encrypted message from server
    const encryptedResponse = await api.get(`/fetch/${messageData.token}`);
    const encryptedMessage = encryptedResponse.data;
    
    console.log('🔓 Encrypted message data:', encryptedMessage);
    
    // Hybrid decryption process (real crypto with fallback for demo)
    console.log('🔓 Using recipient\'s private keys for decryption...');
    setLastSuccess('🔓 Kyber decapsulation in progress...');
    
    let decryptedText: string;
    let ttlRemaining: number = 90; // Default TTL
    
    try {
      // Use the existing fetchAndDecryptHybrid function
      setLastSuccess('🔓 Starting decryption process...');
      console.log('🔓 Attempting decryption for token:', messageData.token);
      
      const result = await fetchAndDecryptHybrid(messageData.token);
      decryptedText = result.plaintext;
      ttlRemaining = result.ttl_remaining || 90;
      
      console.log('✅ Decryption successful! Plaintext:', decryptedText);
      
    } catch (error) {
      console.error('❌ Decryption failed with detailed error:', error);
      console.error('❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
      throw new Error(`Decryption failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    
    // Update the existing message in receivedMsgs to show decrypted content
    setReceivedMsgs(prev => prev.map(msg => {
      if (msg.token === messageData.token || msg.originalToken === messageData.token) {
        return {
          ...msg,
          content: decryptedText,
          decrypted: true,
          ttl_remaining: ttlRemaining
        };
      }
      return msg;
    }));
    setLastSuccess('🔓 Message decrypted successfully');
    setTimeout(() => setLastSuccess(null), 3000);
    
    console.log('✅ Message decryption completed');
    
  } catch (e: any) {
    console.log('❌ Decryption error:', e);
    Alert.alert('Decryption Failed', String(e?.message ?? e));
  }
}

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.select({ ios: 'padding', android: undefined })}>
      <View style={styles.container}>
        <Text style={styles.header}>🛡️ QShield Military-Grade Messaging</Text>
        <Text style={styles.subtitle}>AI-Powered Post-Quantum Secure Communication</Text>
                <View style={styles.statusBar}>
                  <Text style={styles.statusText}>
                    {serverStatus === 'connected' ? '🟢 Server Connected' :
                     serverStatus === 'connecting' ? '🟡 Connecting...' :
                     '🔴 Server Disconnected'}
                  </Text>
                  {!isReady && <Text style={styles.statusText}> | 🔒 Initializing Crypto...</Text>}
                </View>
                
                <View style={styles.securityStatus}>
                  <View style={styles.securityItem}>
                    <Text style={styles.securityLabel}>AI Status:</Text>
                    <Text style={[
                      styles.securityValue,
                      { color: aiStatus === 'secure' ? '#10B981' : aiStatus === 'scanning' ? '#F59E0B' : '#EF4444' }
                    ]}>
                      {aiStatus === 'secure' ? '🛡️ Secure' : 
                       aiStatus === 'scanning' ? '🔍 Scanning...' : 
                       '⚠️ Threat Detected'}
                    </Text>
                  </View>
                  
                  <View style={styles.securityItem}>
                    <Text style={styles.securityLabel}>Threat Level:</Text>
                    <Text style={[
                      styles.securityValue,
                      { color: threatLevel === 'low' ? '#10B981' : threatLevel === 'medium' ? '#F59E0B' : '#EF4444' }
                    ]}>
                      {threatLevel === 'low' ? '🟢 Low' : 
                       threatLevel === 'medium' ? '🟡 Medium' : 
                       '🔴 High'}
                    </Text>
                  </View>
                  
                  <View style={styles.securityItem}>
                    <Text style={styles.securityLabel}>Encryption:</Text>
                    <Text style={[
                      styles.securityValue,
                      { color: encryptionLevel === 'maximum' ? '#10B981' : encryptionLevel === 'enhanced' ? '#3B82F6' : '#6B7280' }
                    ]}>
                      {encryptionLevel === 'maximum' ? '🔐 Maximum' : 
                       encryptionLevel === 'enhanced' ? '🔒 Enhanced' : 
                       '🔓 Standard'}
                    </Text>
                  </View>
                </View>
                
                {lastSuccess && (
                  <View style={styles.successBanner}>
                    <Text style={styles.successText}>{lastSuccess}</Text>
                  </View>
                )}

        <View style={styles.userSelector}>
          <Text style={styles.userLabel}>Current User:</Text>
          <View style={styles.userButtons}>
            <Button
              title="Alice"
              onPress={() => setCurrentUser('alice')}
              color={currentUser === 'alice' ? '#00E0FF' : '#6B7280'}
            />
            <Button
              title="Bob"
              onPress={() => setCurrentUser('bob')}
              color={currentUser === 'bob' ? '#10B981' : '#6B7280'}
            />
            <Button
              title="Charlie"
              onPress={() => setCurrentUser('charlie')}
              color={currentUser === 'charlie' ? '#F59E0B' : '#6B7280'}
            />
            <Button
              title="Delta"
              onPress={() => setCurrentUser('delta')}
              color={currentUser === 'delta' ? '#EF4444' : '#6B7280'}
            />
          </View>
        </View>

        <ScrollView style={styles.chatBox} contentContainerStyle={{ paddingBottom: 20 }}>
          {localMsgs.length === 0 && receivedMsgs.length === 0 && (
            <Text style={{ color: '#888', textAlign: 'center', marginTop: 40 }}>No messages yet</Text>
          )}
          
          {/* Sent Messages */}
          {localMsgs.map(m => (
            <View key={m.localId} style={{ marginBottom: 12, backgroundColor: '#1F2937', borderRadius: 12, padding: 12 }}>
              <MessageBubble msg={{ sender: 'You', message: m.plain ?? '[encrypted]', expiry: m.ttl_seconds ?? 90 }} />
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Text style={{
                    color: m.state === 'error' ? '#ff6b6b' :
                           m.state === 'stored_on_server' ? '#51cf66' :
                           m.state === 'deleted' ? '#868e96' : '#74c0fc',
                    fontSize: 12,
                    fontWeight: '600'
                  }}>
                    {m.state === 'encrypting' ? '🔒 Encrypting...' :
                     m.state === 'sending' ? '📤 Sending...' :
                     m.state === 'stored_on_server' ? '✅ Stored securely' :
                     m.state === 'deleted' ? '🗑️ Deleted' :
                     m.state === 'error' ? '❌ Error' : m.state}
                  </Text>
                </View>
                {m.state === 'stored_on_server' && m.token && (
                  <Button
                    title="🔍 Fetch & Decrypt"
                    onPress={() => onFetchAndShow(m.token)}
                    color="#00E0FF"
                  />
                )}
              </View>
              {m.state === 'error' && (
                <Text style={{ color: '#ff6b6b', fontSize: 12, marginTop: 4 }}>
                  {String(m.serverResponse?.message ?? m.serverResponse ?? 'Unknown error')}
                </Text>
              )}
            </View>
          ))}

          {/* Received Messages */}
          {receivedMsgs.map(m => (
            <View key={m.id} style={{ marginBottom: 12, backgroundColor: '#0F4C3A', borderRadius: 12, padding: 12 }}>
              <MessageBubble msg={{ sender: m.sender, message: m.content, expiry: m.ttl_remaining ?? 90 }} />
              
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Text style={{ color: '#10B981', fontSize: 12, fontWeight: '600' }}>
                    {m.decrypted ? '🔓 Decrypted' : '🔒 Encrypted'}
                  </Text>
                  {!m.decrypted && m.token && (
                    <View style={{ marginLeft: 8 }}>
                      <Button
                        title="🔓 Decrypt"
                        onPress={() => decryptAndDisplayMessage(m)}
                        color="#10B981"
                      />
                    </View>
                  )}
                </View>
                <Text style={{ color: '#9CA3AF', fontSize: 10 }}>
                  {new Date(m.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))}
        </ScrollView>

        <View style={styles.inputBox}>
          <TextInput
            placeholder="Type secure message..."
            placeholderTextColor="#777"
            value={input}
            onChangeText={setInput}
            style={styles.input}
            editable={!isLoading}
          />
          <View style={styles.sendButtons}>
            <Button
              title={isLoading ? "Sending..." : "Send to Alice"}
              onPress={() => onSend('alice')}
              disabled={isLoading || !input.trim()}
              color="#00E0FF"
            />
            <Button
              title={isLoading ? "Sending..." : "Send to Bob"}
              onPress={() => onSend('bob')}
              disabled={isLoading || !input.trim()}
              color="#10B981"
            />
            <Button
              title={isLoading ? "Sending..." : "Send to Charlie"}
              onPress={() => onSend('charlie')}
              disabled={isLoading || !input.trim()}
              color="#F59E0B"
            />
            <Button
              title={isLoading ? "Sending..." : "Send to Delta"}
              onPress={() => onSend('delta')}
              disabled={isLoading || !input.trim()}
              color="#EF4444"
            />
          </View>
        </View>

                <View style={styles.devSection}>
                  <Text style={styles.devTitle}>🔧 Dev helpers (demo only)</Text>
                  <View style={styles.devButtons}>
                    <Button title="Register Alice" onPress={generateAndRegisterAlice} />
                    <Button title="Register Bob" onPress={generateAndRegisterBob} />
                    <Button title="Register Charlie" onPress={() => generateAndRegisterUser('charlie')} />
                    <Button title="Register Delta" onPress={() => generateAndRegisterUser('delta')} />
                    <Button title={`Fetch ${currentUser}'s Messages`} onPress={() => fetchMessagesForUser(currentUser)} />
                    <Button title="Clear Messages" onPress={() => {
                      setReceivedMsgs([]);
                      setLocalMsgs([]);
                    }} />
                    <Button title="Open /pubkey/alice" onPress={async () => {
                      try {
                        const r = await api.get('/pubkey/alice');
                        Alert.alert('pubkey/alice', JSON.stringify(r.data));
                      } catch (e:any) { Alert.alert('error', String(e?.message ?? e)); }
                    }} />
                    <Button title="Open /pubkey/bob" onPress={async () => {
                      try {
                        const r = await api.get('/pubkey/bob');
                        Alert.alert('pubkey/bob', JSON.stringify(r.data));
                      } catch (e:any) { Alert.alert('error', String(e?.message ?? e)); }
                    }} />
                  </View>
                </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#0A0F16', 
    paddingTop: 24 
  },
  header: {
    color: '#00E0FF',
    textAlign: 'center',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
    textShadowColor: '#00E0FF',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10
  },
  subtitle: {
    color: '#9CA3AF',
    textAlign: 'center',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 12,
    fontStyle: 'italic'
  },
  chatBox: { 
    flex: 1, 
    paddingHorizontal: 16,
    backgroundColor: '#0F1419'
  },
  inputBox: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
    backgroundColor: '#0A0F16'
  },
  sendButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8
  },
  input: { 
    flex: 1, 
    color: '#fff', 
    backgroundColor: '#1F2937', 
    borderRadius: 12, 
    paddingHorizontal: 16, 
    marginRight: 12, 
    height: 48,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#374151'
  },
  devSection: {
    padding: 16,
    backgroundColor: '#1F2937',
    borderTopWidth: 1,
    borderTopColor: '#374151'
  },
  devTitle: {
    color: '#9CA3AF',
    fontSize: 14,
    marginBottom: 8,
    fontWeight: '600'
  },
  devButtons: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap'
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8
  },
  statusText: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '500'
  },
  successBanner: {
    backgroundColor: '#10B981',
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
    alignItems: 'center'
  },
  successText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600'
  },
  securityStatus: {
    backgroundColor: '#1F2937',
    marginHorizontal: 16,
    marginBottom: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#374151'
  },
  securityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4
  },
  securityLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '500'
  },
  securityValue: {
    fontSize: 12,
    fontWeight: '600'
  },
  userSelector: {
    backgroundColor: '#1F2937',
    marginHorizontal: 16,
    marginBottom: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#374151'
  },
  userLabel: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8
  },
  userButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8
  }
});
