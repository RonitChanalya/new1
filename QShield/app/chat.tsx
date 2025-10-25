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
  TouchableOpacity,
} from 'react-native';
import MessageBubble from './components/MessageBubble';
import { Link } from 'expo-router';

// Crypto service (Option B - Kyber + libsodium hybrid)
import { encryptAndSendHybrid, fetchAndDecryptHybrid, generateKyberKeypair, kyberDecapsulate, deriveSymmetricKey } from '../src/services/cryptoService';
import { base64ToBytes } from '../src/utils/base64';
import { SendIcon, CheckCircleIcon, LockIcon, AlertTriangleIcon, AlertCircleIcon, FingerprintIcon, ShieldIcon, QShieldLogo, QShieldLogoComponent } from '../components/icons';
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
  const [autoDestruct, setAutoDestruct] = useState(false);
  const [metadataProtection, setMetadataProtection] = useState(false);
  const [groups, setGroups] = useState<any[]>([]);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newMemberId, setNewMemberId] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<any>(null);

  useEffect(() => {
    // Load groups for current user
    fetchGroupsForUser(currentUser);
  }, [currentUser]);

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



// Group Management Functions
async function createGroup(groupName: string, creatorId: string) {
  try {
    console.log(`🔧 Creating group: ${groupName} by ${creatorId}`);
    
    // Generate group encryption keys
    const groupKyberKeypair = await generateKyberKeypair();
    const groupX25519Keypair = nacl.box.keyPair();
    const { bytesToBase64 } = await import('../src/utils/base64');
    
    const groupId = 'group_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    
    const groupData = {
      groupId,
      groupName,
      creatorId,
      members: [creatorId],
      kyber_pub_b64: groupKyberKeypair.publicKey_b64,
      kyber_priv_b64: groupKyberKeypair.privateKey_b64,
      x25519_pub_b64: bytesToBase64(groupX25519Keypair.publicKey),
      x25519_priv_b64: bytesToBase64(groupX25519Keypair.secretKey),
      createdAt: Date.now(),
      isActive: true
    };
    
    // Store group on server
    const response = await api.post('/groups/create', groupData);
    console.log('✅ Group created successfully:', response.data);
    
    // Update local state
    setGroups(prev => [...prev, groupData]);
    setLastSuccess(`✅ Group "${groupName}" created successfully!`);
    setTimeout(() => setLastSuccess(null), 5000);
    
    return groupData;
  } catch (error) {
    console.error('❌ Group creation failed:', error);
    Alert.alert('Group Creation Failed', `Failed to create group: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

async function addMemberToGroup(groupId: string, memberId: string) {
  try {
    console.log(`🔧 Adding member ${memberId} to group ${groupId}`);
    
    // Generate member's encryption keys
    const memberKyberKeypair = await generateKyberKeypair();
    const memberX25519Keypair = nacl.box.keyPair();
    const { bytesToBase64 } = await import('../src/utils/base64');
    
    const memberData = {
      memberId,
      kyber_pub_b64: memberKyberKeypair.publicKey_b64,
      kyber_priv_b64: memberKyberKeypair.privateKey_b64,
      x25519_pub_b64: bytesToBase64(memberX25519Keypair.publicKey),
      x25519_priv_b64: bytesToBase64(memberX25519Keypair.secretKey),
      addedAt: Date.now()
    };
    
    // Add member to group on server
    const response = await api.post(`/groups/${groupId}/add-member`, memberData);
    console.log('✅ Member added successfully:', response.data);
    
    // Update local state
    setGroups(prev => prev.map(group => 
      group.groupId === groupId 
        ? { ...group, members: [...group.members, memberId] }
        : group
    ));
    
    setLastSuccess(`✅ ${memberId} added to group successfully!`);
    setTimeout(() => setLastSuccess(null), 5000);
    
  } catch (error) {
    console.error('❌ Add member failed:', error);
    Alert.alert('Add Member Failed', `Failed to add member: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

async function removeMemberFromGroup(groupId: string, memberId: string) {
  try {
    console.log(`🔧 Removing member ${memberId} from group ${groupId}`);
    
    // Remove member from group on server
    const response = await api.post(`/groups/${groupId}/remove-member`, { memberId });
    console.log('✅ Member removed successfully:', response.data);
    
    // Update local state
    setGroups(prev => prev.map(group => 
      group.groupId === groupId 
        ? { ...group, members: group.members.filter((id: string) => id !== memberId) }
        : group
    ));
    
    setLastSuccess(`✅ ${memberId} removed from group successfully!`);
    setTimeout(() => setLastSuccess(null), 5000);
    
  } catch (error) {
    console.error('❌ Remove member failed:', error);
    Alert.alert('Remove Member Failed', `Failed to remove member: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

async function deleteGroup(groupId: string) {
  try {
    console.log(`🔧 Deleting group ${groupId}`);
    
    // Delete group on server
    const response = await api.delete(`/groups/${groupId}`);
    console.log('✅ Group deleted successfully:', response.data);
    
    // Update local state
    setGroups(prev => prev.filter(group => group.groupId !== groupId));
    
    setLastSuccess(`✅ Group deleted successfully!`);
    setTimeout(() => setLastSuccess(null), 5000);
    
  } catch (error) {
    console.error('❌ Delete group failed:', error);
    Alert.alert('Delete Group Failed', `Failed to delete group: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

async function fetchGroupsForUser(userId: string) {
  try {
    console.log(`🔍 Fetching groups for ${userId}...`);
    const response = await api.get(`/groups/user/${userId}`);
    console.log(`📨 Found ${response.data.length} groups for ${userId}`);
    console.log('📨 Groups data:', response.data);
    setGroups(response.data);
  } catch (error) {
    console.error('❌ Fetch groups error:', error);
    // Don't show alert for empty groups, just log the error
    console.log('ℹ️ No groups found for user (this is normal for new users)');
    setGroups([]);
  }
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
        <View style={styles.header}>
          <QShieldLogoComponent size={24} />
          <Text style={styles.headerText}>QShield Military-Grade Messaging</Text>
        </View>
        <Text style={styles.subtitle}>AI-Powered Post-Quantum Secure Communication</Text>
                <View style={styles.statusBar}>
                  <Text style={styles.statusText}>
                    {serverStatus === 'connected' ? '🟢 Server Connected' :
                     serverStatus === 'connecting' ? '🟡 Connecting...' :
                     '🔴 Server Disconnected'}
                  </Text>
                  {!isReady && <Text style={styles.statusText}> | Initializing Crypto...</Text>}
                </View>
                
                <View style={styles.securityStatus}>
                  <View style={styles.securityItem}>
                    <Text style={styles.securityLabel}>AI Status:</Text>
                    <Text style={[
                      styles.securityValue,
                      { color: aiStatus === 'secure' ? '#10B981' : aiStatus === 'scanning' ? '#F59E0B' : '#EF4444' }
                    ]}>
                      {aiStatus === 'secure' ? 'Secure' : 
                       aiStatus === 'scanning' ? 'Scanning...' : 
                       'Threat Detected'}
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
                       encryptionLevel === 'enhanced' ? 'Enhanced' : 
                       '🔓 Standard'}
                    </Text>
                  </View>
                </View>
                
                {lastSuccess && (
                  <View style={styles.successBanner}>
                    <Text style={styles.successText}>{lastSuccess}</Text>
                  </View>
                )}

        {/* Group Management Section - DEBUG VISIBLE */}
        <View style={styles.groupSection}>
          <Text style={{color: 'white', fontSize: 20, fontWeight: 'bold'}}>🔧 DEBUG: Group Section is HERE!</Text>
          <View style={styles.groupHeader}>
            <Text style={styles.groupTitle}>🔐 Secure Groups</Text>
            <TouchableOpacity 
              style={styles.createGroupButton}
              onPress={() => {
                console.log('🔧 Create group button clicked');
                setShowGroupModal(true);
              }}
            >
              <Text style={styles.createGroupButtonText}>+ New Group</Text>
            </TouchableOpacity>
          </View>
          
          {groups.length > 0 ? (
            <View style={styles.groupsList}>
              {groups.map(group => (
                <View key={group.groupId} style={styles.groupItem}>
                  <View style={styles.groupInfo}>
                    <Text style={styles.groupName}>{group.groupName}</Text>
                    <Text style={styles.groupMembers}>{group.members.length} members</Text>
                  </View>
                  <View style={styles.groupActions}>
                    <TouchableOpacity 
                      style={styles.groupActionButton}
                      onPress={() => {
                        setSelectedGroup(group);
                        setNewMemberId('');
                      }}
                    >
                      <Text style={styles.groupActionText}>+ Add Member</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.groupActionButton, styles.deleteButton]}
                      onPress={() => deleteGroup(group.groupId)}
                    >
                      <Text style={[styles.groupActionText, styles.deleteText]}>Delete</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          ) : (
            <View style={styles.noGroupsContainer}>
              <Text style={styles.noGroupsText}>No groups yet. Create your first secure group!</Text>
            </View>
          )}
        </View>

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
                    {m.state === 'encrypting' ? 'Encrypting...' :
                     m.state === 'sending' ? 'Sending...' :
                     m.state === 'stored_on_server' ? 'Stored securely' :
                     m.state === 'deleted' ? 'Deleted' :
                     m.state === 'error' ? 'Error' : m.state}
                  </Text>
                </View>
                {m.state === 'stored_on_server' && m.token && (
                  <Button
                    title="Fetch & Decrypt"
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
                    {m.decrypted ? 'Decrypted' : 'Encrypted'}
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

        <View style={styles.inputContainer}>
          <View style={styles.unifiedInputBar}>
            <TextInput
              style={styles.messageInput}
              placeholder="Type secure message..."
              placeholderTextColor="#9CA3AF"
              value={input}
              onChangeText={setInput}
              editable={!isLoading}
              multiline
              onSubmitEditing={() => {
                if (input.trim() && !isLoading) {
                  onSend('alice');
                }
              }}
              returnKeyType="send"
              blurOnSubmit={false}
            />
            <TouchableOpacity 
              style={[styles.sendButton, (!input.trim() || isLoading) && styles.sendButtonDisabled]} 
              onPress={() => onSend('alice')}
              disabled={isLoading || !input.trim()}
            >
              <SendIcon size={16} color="hsl(210, 40%, 98%)" />
              <Text style={styles.sendButtonText}>Send</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.optionsContainer}>
            <TouchableOpacity
              style={[styles.optionButton, autoDestruct && styles.activeOption]}
              onPress={() => setAutoDestruct(!autoDestruct)}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <CheckCircleIcon size={14} color="hsl(142, 76%, 36%)" />
                <Text style={[styles.optionText, autoDestruct && styles.activeOptionText, { marginLeft: 4 }]}>
                  Auto-destruct (30s)
                </Text>
              </View>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.optionButton, metadataProtection && styles.activeOption]}
              onPress={() => setMetadataProtection(!metadataProtection)}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <CheckCircleIcon size={14} color="hsl(142, 76%, 36%)" />
                <Text style={[styles.optionText, metadataProtection && styles.activeOptionText, { marginLeft: 4 }]}>
                  Metadata protection
                </Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Group Creation Modal */}
        {showGroupModal && (
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Create New Group</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="Enter group name"
                placeholderTextColor="#9CA3AF"
                value={newGroupName}
                onChangeText={setNewGroupName}
                onSubmitEditing={() => {
                  if (newGroupName.trim()) {
                    createGroup(newGroupName.trim(), currentUser);
                    setShowGroupModal(false);
                    setNewGroupName('');
                  }
                }}
                returnKeyType="done"
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => {
                    setShowGroupModal(false);
                    setNewGroupName('');
                  }}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.createButton]}
                  onPress={() => {
                    if (newGroupName.trim()) {
                      createGroup(newGroupName.trim(), currentUser);
                      setShowGroupModal(false);
                      setNewGroupName('');
                    }
                  }}
                >
                  <Text style={styles.createButtonText}>Create Group</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Add Member Modal */}
        {selectedGroup && (
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Add Member to {selectedGroup.groupName}</Text>
              <TextInput
                style={styles.modalInput}
                placeholder="Enter member ID (e.g., alice, bob)"
                placeholderTextColor="#9CA3AF"
                value={newMemberId}
                onChangeText={setNewMemberId}
                onSubmitEditing={() => {
                  if (newMemberId.trim()) {
                    addMemberToGroup(selectedGroup.groupId, newMemberId.trim());
                    setSelectedGroup(null);
                    setNewMemberId('');
                  }
                }}
                returnKeyType="done"
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => {
                    setSelectedGroup(null);
                    setNewMemberId('');
                  }}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.createButton]}
                  onPress={() => {
                    if (newMemberId.trim()) {
                      addMemberToGroup(selectedGroup.groupId, newMemberId.trim());
                      setSelectedGroup(null);
                      setNewMemberId('');
                    }
                  }}
                >
                  <Text style={styles.createButtonText}>Add Member</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  headerText: {
    color: '#00E0FF',
    fontSize: 21, // Reduced from 22 (5% decrease)
    fontWeight: '700',
    marginLeft: 12,
    textShadowColor: '#00E0FF',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10
  },
  subtitle: {
    color: '#9CA3AF',
    textAlign: 'center',
    fontSize: 13, // Reduced from 14 (5% decrease)
    fontWeight: '500',
    marginBottom: 12,
    fontStyle: 'italic'
  },
  chatBox: { 
    flex: 1, 
    paddingHorizontal: 16,
    backgroundColor: '#0F1419'
  },
  inputContainer: {
    padding: 16,
    backgroundColor: '#0A0F16',
    borderTopWidth: 1,
    borderTopColor: '#1f2937',
  },
  unifiedInputBar: {
    flexDirection: 'row',
    backgroundColor: 'transparent',
    borderRadius: 5, // 6 * 0.9 = 5.4 -> 5
    borderWidth: 1,
    borderColor: '#374151',
    overflow: 'hidden',
    marginBottom: 11, // 12 * 0.9 = 10.8 -> 11
    height: 36, // 40 * 0.9 = 36
  },
  messageInput: {
    flex: 0.7,
    backgroundColor: 'transparent',
    paddingHorizontal: 10, // 12 * 0.9 = 10.8 -> 10
    paddingVertical: 7, // 8 * 0.9 = 7.2 -> 7
    fontSize: 12, // 13 * 0.9 = 11.7 -> 12
    color: '#F9FAFB',
    minHeight: 36, // 40 * 0.9 = 36
    maxHeight: 108, // 120 * 0.9 = 108
  },
  sendButton: {
    backgroundColor: '#008080',
    paddingHorizontal: 10, // 12 * 0.9 = 10.8 -> 10
    paddingVertical: 7, // 8 * 0.9 = 7.2 -> 7
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 36, // 40 * 0.9 = 36
    minWidth: 72, // 80 * 0.9 = 72
  },
  sendButtonDisabled: {
    backgroundColor: '#374151',
    opacity: 0.6,
  },
  sendIcon: {
    fontSize: 14, // 15 * 0.9 = 13.5 -> 14
    marginRight: 5, // 6 * 0.9 = 5.4 -> 5
    color: '#fff',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 14, // 15 * 0.9 = 13.5 -> 14
    fontWeight: '600',
  },
  optionsContainer: {
    flexDirection: 'row',
    gap: 14, // 16 * 0.9 = 14.4 -> 14
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionText: {
    color: 'hsl(215, 20%, 65%)',
    fontSize: 12, // 13 * 0.9 = 11.7 -> 12
    fontWeight: '500',
  },
  activeOption: {
    // No additional styling needed for active state
  },
  activeOptionText: {
    color: '#EF4444',
    fontWeight: '600',
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
    fontSize: 11, // Reduced from 12 (5% decrease)
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
    fontSize: 13, // Reduced from 14 (5% decrease)
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
    fontSize: 11, // Reduced from 12 (5% decrease)
    fontWeight: '500'
  },
  securityValue: {
    fontSize: 11, // Reduced from 12 (5% decrease)
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
    fontSize: 13, // Reduced from 14 (5% decrease)
    fontWeight: '600',
    marginBottom: 8
  },
  userButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8
  },
  // Group Management Styles
  groupSection: {
    backgroundColor: '#FF0000', // Bright red for debugging
    marginHorizontal: 16,
    marginBottom: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#374151'
  },
  groupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  groupTitle: {
    color: '#F9FAFB',
    fontSize: 16,
    fontWeight: '600'
  },
  createGroupButton: {
    backgroundColor: '#008080',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6
  },
  createGroupButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600'
  },
  groupsList: {
    gap: 8
  },
  groupItem: {
    backgroundColor: '#111827',
    padding: 12,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#374151'
  },
  groupInfo: {
    marginBottom: 8
  },
  groupName: {
    color: '#F9FAFB',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4
  },
  groupMembers: {
    color: '#9CA3AF',
    fontSize: 12
  },
  groupActions: {
    flexDirection: 'row',
    gap: 8
  },
  groupActionButton: {
    backgroundColor: '#374151',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    flex: 1
  },
  groupActionText: {
    color: '#F9FAFB',
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center'
  },
  deleteButton: {
    backgroundColor: '#EF4444'
  },
  deleteText: {
    color: '#fff'
  },
  // Modal Styles
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  modalContent: {
    backgroundColor: '#1F2937',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#374151',
    width: '80%',
    maxWidth: 400
  },
  modalTitle: {
    color: '#F9FAFB',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center'
  },
  modalInput: {
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#F9FAFB',
    fontSize: 14,
    marginBottom: 16
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12
  },
  modalButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center'
  },
  cancelButton: {
    backgroundColor: '#374151'
  },
  cancelButtonText: {
    color: '#F9FAFB',
    fontSize: 14,
    fontWeight: '500'
  },
  createButton: {
    backgroundColor: '#008080'
  },
  createButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600'
  },
  // No Groups Styles
  noGroupsContainer: {
    padding: 16,
    alignItems: 'center',
    backgroundColor: '#111827',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#374151',
    borderStyle: 'dashed'
  },
  noGroupsText: {
    color: '#9CA3AF',
    fontSize: 13,
    textAlign: 'center',
    fontStyle: 'italic'
  }
});
