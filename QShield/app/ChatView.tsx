import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from 'react-native';
import { encryptAndSendHybrid, fetchAndDecryptHybrid, generateKyberKeypair } from '../src/services/cryptoService';
import MessageBubble from './components/MessageBubble';
import api from '../src/api';
import * as nacl from 'tweetnacl';
import { bytesToBase64 } from '../src/utils/base64';
import { LockIcon, ActivityIcon, AlertTriangleIcon, UsersIcon, SendIcon, CheckCircleIcon } from '../components/icons';

interface Message {
  id: string;
  sender: string;
  content: string;
  timestamp: number;
  decrypted: boolean;
  token?: string;
  ttl_remaining?: number;
}

interface Channel {
  id: string;
  name: string;
  lastMessage: string;
  unreadCount: number;
  isActive: boolean;
}

export default function ChatView() {
  const [channels, setChannels] = useState<Channel[]>([
    { id: 'alpha', name: 'Alpha Team', lastMessage: 'Coordinates confirmed', unreadCount: 3, isActive: true },
    { id: 'command', name: 'Command HQ', lastMessage: 'Mission briefing at 0600', unreadCount: 0, isActive: false },
    { id: 'bravo', name: 'Bravo Squad', lastMessage: 'Supplies en route', unreadCount: 1, isActive: false },
  ]);

  const [activeChannel, setActiveChannel] = useState('alpha');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [autoDestruct, setAutoDestruct] = useState(true);
  const [metadataProtection, setMetadataProtection] = useState(true);
  const [groups, setGroups] = useState<any[]>([]);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState<string[]>([]);
  const [currentMemberId, setCurrentMemberId] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [groupToDelete, setGroupToDelete] = useState<string | null>(null);
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('');

  // Group Management Functions
  const createGroup = async (groupName: string, creatorId: string) => {
    try {
      console.log(`🔧 Creating group: ${groupName} by ${creatorId}`);
      
      const groupKyberKeypair = await generateKyberKeypair();
      const groupX25519Keypair = nacl.box.keyPair();
      
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
      
      const response = await api.post('/groups/create', groupData);
      console.log('✅ Group created successfully:', response.data);
      
      setGroups(prev => [...prev, groupData]);
      
      // Add group as a new channel
      const newChannel: Channel = {
        id: groupId,
        name: groupName,
        lastMessage: 'Group created',
        unreadCount: 0,
        isActive: false
      };
      setChannels(prev => [...prev, newChannel]);
      
      Alert.alert('Success', `Group "${groupName}" created successfully! It's now available as a channel.`);
      
      return groupData;
    } catch (error) {
      console.error('❌ Group creation failed:', error);
      Alert.alert('Group Creation Failed', `Failed to create group: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const addMemberToGroup = async (groupId: string, memberId: string) => {
    try {
      console.log(`🔧 Adding member ${memberId} to group ${groupId}`);
      
      const memberKyberKeypair = await generateKyberKeypair();
      const memberX25519Keypair = nacl.box.keyPair();
      
      const memberData = {
        memberId,
        kyber_pub_b64: memberKyberKeypair.publicKey_b64,
        kyber_priv_b64: memberKyberKeypair.privateKey_b64,
        x25519_pub_b64: bytesToBase64(memberX25519Keypair.publicKey),
        x25519_priv_b64: bytesToBase64(memberX25519Keypair.secretKey),
        addedAt: Date.now()
      };
      
      const response = await api.post(`/groups/${groupId}/add-member`, memberData);
      console.log('✅ Member added successfully:', response.data);
      
      setGroups(prev => prev.map(group => 
        group.groupId === groupId 
          ? { ...group, members: [...group.members, memberId] }
          : group
      ));
      
      Alert.alert('Success', `${memberId} added to group successfully!`);
      
    } catch (error) {
      console.error('❌ Add member failed:', error);
      Alert.alert('Add Member Failed', `Failed to add member: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const deleteGroup = async (groupId: string) => {
    try {
      console.log(`🔧 Deleting group ${groupId}`);
      
      const response = await api.delete(`/groups/${groupId}`);
      console.log('✅ Group deleted successfully:', response.data);
      
      setGroups(prev => prev.filter(group => group.groupId !== groupId));
      
      // Remove group from channels
      setChannels(prev => prev.filter(channel => channel.id !== groupId));
      
      Alert.alert('Success', 'Group deleted successfully!');
      
    } catch (error) {
      console.error('❌ Delete group failed:', error);
      Alert.alert('Delete Group Failed', `Failed to delete group: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const addMemberToNewGroup = () => {
    if (currentMemberId.trim() && !newGroupMembers.includes(currentMemberId.trim())) {
      setNewGroupMembers(prev => [...prev, currentMemberId.trim()]);
      setCurrentMemberId('');
    }
  };

  const removeMemberFromNewGroup = (memberId: string) => {
    setNewGroupMembers(prev => prev.filter(id => id !== memberId));
  };

  const createGroupWithMembers = async () => {
    if (newGroupName.trim()) {
      const groupData = await createGroup(newGroupName.trim(), 'bob');
      if (groupData) {
        // Add all members to the group
        for (const memberId of newGroupMembers) {
          await addMemberToGroup(groupData.groupId, memberId);
        }
        setShowGroupModal(false);
        setNewGroupName('');
        setNewGroupMembers([]);
        setCurrentMemberId('');
      }
    }
  };

  const handleDeleteGroupChannel = (channelId: string) => {
    if (channelId.startsWith('group_')) {
      setGroupToDelete(channelId);
      setShowDeleteConfirm(true);
    }
  };

  const confirmDeleteGroup = async () => {
    if (groupToDelete && deleteConfirmationText === 'Delete') {
      await deleteGroup(groupToDelete);
      setShowDeleteConfirm(false);
      setGroupToDelete(null);
      setDeleteConfirmationText('');
    }
  };

  const loadMessages = async () => {
    try {
      const response = await api.get('/messages/bob');
      if (response.data && Array.isArray(response.data)) {
        const processedMessages = response.data.map((msg: any) => ({
          id: msg.id || msg.token,
          sender: msg.sender || 'Unknown',
          content: msg.content || '[ENCRYPTED]',
          timestamp: msg.timestamp || Date.now(),
          decrypted: msg.decrypted || false,
          token: msg.token,
          ttl_remaining: msg.ttl_remaining || 30,
        }));
        setMessages(processedMessages);
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  useEffect(() => {
    loadMessages();
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    try {
      console.log('🔐 Sending encrypted message:', inputMessage);
      const { token, serverResponse } = await encryptAndSendHybrid(inputMessage, 'bob', { ttl_seconds: 30 });
      console.log('✅ Message sent successfully:', { token, serverResponse });
      
      setInputMessage('');
      
      // Add the sent message to local state immediately
      const messageContent = inputMessage; // Store before clearing
      const newMessage: Message = {
        id: token || `msg_${Date.now()}`,
        sender: 'You',
        content: messageContent,
        timestamp: Date.now(),
        decrypted: true, // Sent messages are already decrypted for display
        token: token,
        ttl_remaining: 30
      };
      
      setMessages(prev => [newMessage, ...prev]);
      
      // Also reload messages from server to get any new received messages
      loadMessages();
      
    } catch (error) {
      console.error('❌ Send error:', error);
      Alert.alert('Send Failed', `Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDecryptMessage = async (message: Message) => {
    if (!message.token) return;

    try {
      const result = await fetchAndDecryptHybrid(message.token);
      // Update the message in the local state
      setMessages(prev => prev.map(msg => 
        msg.id === message.id 
          ? { ...msg, content: result.plaintext, decrypted: true }
          : msg
      ));
    } catch (error) {
      console.error('Decryption error:', error);
      Alert.alert('Decryption Failed', 'Failed to decrypt message');
    }
  };


  return (
    <View style={styles.container}>
      {/* Channel List */}
      <View style={styles.channelList}>
        <View style={styles.channelHeader}>
          <Text style={styles.channelTitle}>Secure Channels</Text>
          <Text style={styles.channelSubtitle}>End-to-end encrypted</Text>
        </View>

        <ScrollView style={styles.channelScroll}>
          {/* Add Group Tab */}
          <TouchableOpacity 
            style={styles.addGroupTab}
            onPress={() => setShowGroupModal(true)}
          >
            <View style={styles.addGroupTabIcon}>
              <Text style={styles.addGroupTabIconText}>+</Text>
            </View>
            <View style={styles.addGroupTabContent}>
              <Text style={styles.addGroupTabTitle}>Add New Group</Text>
              <Text style={styles.addGroupTabSubtitle}>Create secure group channel</Text>
            </View>
          </TouchableOpacity>
          
          {channels.map((channel) => (
            <TouchableOpacity
              key={channel.id}
              style={[styles.channelItem, activeChannel === channel.id && styles.activeChannelItem]}
              onPress={() => setActiveChannel(channel.id)}
            >
              <View style={styles.channelIcon}>
                {channel.id.startsWith('group_') ? (
                  <UsersIcon size={20} color="hsl(210, 40%, 98%)" />
                ) : (
                  <LockIcon size={20} color="hsl(210, 40%, 98%)" />
                )}
              </View>
              <View style={styles.channelContent}>
                <View style={styles.channelHeaderRow}>
                  <Text style={[styles.channelName, activeChannel === channel.id && styles.activeChannelName]}>
                    {channel.name}
                  </Text>
                  {channel.unreadCount > 0 && (
                    <View style={styles.unreadBadge}>
                      <Text style={styles.unreadText}>{channel.unreadCount}</Text>
                    </View>
                  )}
                </View>
                <Text style={[styles.channelLastMessage, activeChannel === channel.id && styles.activeChannelLastMessage]}>
                  {channel.lastMessage}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>

      </View>

      {/* Chat Area */}
      <View style={styles.chatArea}>
        {/* Chat Header */}
        <View style={styles.chatHeader}>
          <View style={styles.chatHeaderLeft}>
            <Text style={styles.chatTitle}>
              {activeChannel.startsWith('group_') 
                ? channels.find(c => c.id === activeChannel)?.name || 'Group Channel'
                : 'Alpha Team'
              }
            </Text>
            <View style={styles.encryptionTag}>
              <LockIcon size={16} color="hsl(210, 40%, 98%)" />
              <Text style={styles.encryptionText}>E2E Encrypted</Text>
            </View>
          </View>
          <View style={styles.chatHeaderRight}>
            {activeChannel.startsWith('group_') && (
              <TouchableOpacity 
                style={styles.headerDeleteButton}
                onPress={() => handleDeleteGroupChannel(activeChannel)}
              >
                <AlertTriangleIcon size={16} color="#EF4444" />
              </TouchableOpacity>
            )}
            <View style={styles.monitoringStatus}>
              <ActivityIcon size={16} color="hsl(210, 40%, 98%)" />
              <Text style={styles.monitoringText}>AI Monitoring Active</Text>
            </View>
          </View>
        </View>

        {/* Messages */}
        <ScrollView style={styles.messagesContainer}>
          {messages.map((message) => (
            <View key={message.id} style={styles.messageContainer}>
              <MessageBubble 
                msg={{
                  ...message,
                  message: message.content,
                  expiry: message.ttl_remaining || 30, // Use actual TTL
                  sender: message.sender,
                  timestamp: new Date(message.timestamp).toLocaleTimeString()
                }} 
              />
              
              {/* Decryption Controls */}
              <View style={styles.messageControls}>
                <View style={styles.messageStatus}>
                  <Text style={styles.statusText}>
                    {message.decrypted ? 'Decrypted' : 'Encrypted'}
                  </Text>
                  {!message.decrypted && message.token && (
                    <TouchableOpacity
                      style={styles.decryptButton}
                      onPress={() => handleDecryptMessage(message)}
                    >
                      <Text style={styles.decryptButtonText}>🔓 Decrypt</Text>
                    </TouchableOpacity>
                  )}
                </View>
                <Text style={styles.timestamp}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))}
        </ScrollView>

        {/* Message Input */}
        <View style={styles.inputContainer}>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.messageInput}
              placeholder="Type secure message..."
              placeholderTextColor="hsl(215, 20%, 65%)"
              value={inputMessage}
              onChangeText={setInputMessage}
              multiline
              onSubmitEditing={() => {
                if (inputMessage.trim()) {
                  handleSendMessage();
                }
              }}
              returnKeyType="send"
              blurOnSubmit={false}
            />
            <TouchableOpacity style={styles.sendButton} onPress={handleSendMessage}>
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
              
              {/* Group Name Input */}
              <TextInput
                style={styles.modalInput}
                placeholder="Enter group name"
                placeholderTextColor="#9CA3AF"
                value={newGroupName}
                onChangeText={setNewGroupName}
              />
              
              {/* Member Addition Section */}
              <View style={styles.memberSection}>
                <Text style={styles.memberSectionTitle}>Add Members</Text>
                
                {/* Add Member Input */}
                <View style={styles.addMemberRow}>
                  <TextInput
                    style={[styles.modalInput, styles.memberInput]}
                    placeholder="Enter member ID (e.g., alice, charlie)"
                    placeholderTextColor="#9CA3AF"
                    value={currentMemberId}
                    onChangeText={setCurrentMemberId}
                  />
                  <TouchableOpacity 
                    style={styles.addMemberButton}
                    onPress={addMemberToNewGroup}
                  >
                    <Text style={styles.addMemberButtonText}>+</Text>
                  </TouchableOpacity>
                </View>
                
                {/* Members List */}
                {newGroupMembers.length > 0 && (
                  <View style={styles.membersList}>
                    <Text style={styles.membersListTitle}>Members ({newGroupMembers.length}):</Text>
                    {newGroupMembers.map((memberId, index) => (
                      <View key={index} style={styles.memberItem}>
                        <Text style={styles.memberId}>{memberId}</Text>
                        <TouchableOpacity 
                          style={styles.removeMemberButton}
                          onPress={() => removeMemberFromNewGroup(memberId)}
                        >
                          <Text style={styles.removeMemberButtonText}>×</Text>
                        </TouchableOpacity>
                      </View>
                    ))}
                  </View>
                )}
              </View>
              
              <View style={styles.modalButtons}>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => {
                    setShowGroupModal(false);
                    setNewGroupName('');
                    setNewGroupMembers([]);
                    setCurrentMemberId('');
                  }}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.createButton]}
                  onPress={createGroupWithMembers}
                >
                  <Text style={styles.createButtonText}>Create Group</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Delete Group Confirmation Modal */}
        {showDeleteConfirm && (
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Delete Group</Text>
              <Text style={styles.deleteConfirmText}>
                This will permanently delete the group and remove it from all members. This action cannot be undone.
              </Text>
              <Text style={styles.deleteWarningText}>
                Type "Delete" to confirm:
              </Text>
              <TextInput
                style={styles.deleteConfirmInput}
                placeholder="Type Delete here"
                placeholderTextColor="#9CA3AF"
                value={deleteConfirmationText}
                onChangeText={setDeleteConfirmationText}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <View style={styles.modalButtons}>
                <TouchableOpacity 
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => {
                    setShowDeleteConfirm(false);
                    setGroupToDelete(null);
                    setDeleteConfirmationText('');
                  }}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[
                    styles.modalButton, 
                    styles.deleteConfirmButton,
                    deleteConfirmationText !== 'Delete' && styles.disabledButton
                  ]}
                  onPress={confirmDeleteGroup}
                  disabled={deleteConfirmationText !== 'Delete'}
                >
                  <Text style={[
                    styles.deleteConfirmButtonText,
                    deleteConfirmationText !== 'Delete' && styles.disabledButtonText
                  ]}>
                    Delete Group
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
        
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
  },
  channelList: {
    width: 320,
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    padding: 16,
    borderRightWidth: 1,
    borderRightColor: 'hsl(220, 15%, 25%)', // --border
  },
  channelHeader: {
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'hsl(220, 15%, 25%)', // --border
    marginBottom: 16,
  },
  channelTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 4,
  },
  channelSubtitle: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '400',
  },
  channelScroll: {
    flex: 1,
  },
  // Add Group Tab Styles
  addGroupTab: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 8,
    backgroundColor: 'hsl(220, 15%, 20%)', // --muted
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'hsl(142, 76%, 36%)', // --primary
    borderStyle: 'dashed',
    opacity: 0.8,
  },
  addGroupTabIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: 'hsl(142, 76%, 36%)', // --primary
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  addGroupTabIconText: {
    fontSize: 18,
    fontWeight: '300',
    color: 'hsl(142, 76%, 36%)', // --primary
  },
  addGroupTabContent: {
    flex: 1,
  },
  addGroupTabTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: 'hsl(215, 20%, 75%)', // --foreground with slight opacity
    marginBottom: 2,
  },
  addGroupTabSubtitle: {
    fontSize: 12,
    color: 'hsl(215, 20%, 55%)', // --muted-foreground with more opacity
    fontWeight: '400',
  },
  channelItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 0,
    backgroundColor: 'transparent',
    borderRadius: 0,
    borderBottomWidth: 1,
    borderBottomColor: 'hsl(220, 15%, 25%)', // --border
  },
  activeChannelItem: {
    backgroundColor: 'hsl(220, 15%, 20%)', // --muted
  },
  channelIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'hsl(180, 94%, 29%, 0.2)', // --primary with opacity
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  channelIconText: {
    fontSize: 20,
  },
  channelContent: {
    flex: 1,
  },
  channelHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  channelName: {
    fontSize: 14,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 4,
    flex: 1,
  },
  activeChannelName: {
    color: 'hsl(210, 40%, 98%)', // --foreground
  },
  channelLastMessage: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
  },
  activeChannelLastMessage: {
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
  },
  unreadBadge: {
    backgroundColor: 'hsl(180, 94%, 29%)', // --primary
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  unreadText: {
    color: 'hsl(210, 40%, 98%)', // --primary-foreground
    fontSize: 12,
    fontWeight: '700',
  },
  chatArea: {
    flex: 1,
    backgroundColor: 'hsl(217, 45%, 10%)', // --background
  },
  chatHeader: {
    height: 64,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    borderBottomWidth: 1,
    borderBottomColor: 'hsl(220, 15%, 25%)', // --border
  },
  chatHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  chatTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginRight: 12,
  },
  encryptionTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 12,
  },
  encryptionIcon: {
    fontSize: 12,
    marginRight: 4,
  },
  encryptionText: {
    color: 'hsl(210, 40%, 98%)', // --foreground
    fontSize: 12,
    fontWeight: '500',
  },
  monitoringStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  monitoringIcon: {
    fontSize: 16,
    color: 'hsl(150, 70%, 40%)', // --success
  },
  monitoringText: {
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontSize: 12,
    fontWeight: '500',
  },
  messagesContainer: {
    flex: 1,
    padding: 24,
  },
  messageContainer: {
    marginBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 16,
    borderRadius: 6, // --radius
    shadowColor: 'hsl(220, 25%, 8%)',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 2,
  },
  sentMessage: {
    backgroundColor: 'hsl(180, 94%, 29%, 0.2)', // --primary with opacity
    alignSelf: 'flex-end',
  },
  receivedMessage: {
    backgroundColor: 'hsl(220, 20%, 15%)', // --card
    alignSelf: 'flex-start',
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  senderName: {
    fontSize: 12,
    fontWeight: '600',
    color: 'hsl(210, 40%, 98%)', // --foreground
    flex: 1,
  },
  encryptedIcon: {
    fontSize: 12,
    color: 'hsl(150, 70%, 40%)', // --success
    marginLeft: 4,
  },
  timerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  timerIcon: {
    fontSize: 10,
    marginRight: 2,
  },
  timerText: {
    fontSize: 10,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
  },
  messageText: {
    fontSize: 14,
    color: 'hsl(210, 40%, 98%)', // --foreground
    marginBottom: 6,
    lineHeight: 20,
  },
  messageTime: {
    fontSize: 10,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
  },
  decryptButton: {
    backgroundColor: 'hsl(150, 70%, 40%)', // --success
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  decryptButtonText: {
    color: 'hsl(210, 40%, 98%)', // --success-foreground
    fontSize: 12,
    fontWeight: '600',
  },
  messageControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 4,
  },
  messageStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusText: {
    color: 'hsl(150, 70%, 40%)', // --success
    fontSize: 12,
    fontWeight: '600',
  },
  timestamp: {
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontSize: 10,
  },
  inputContainer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: 'hsl(220, 15%, 25%)', // --border
  },
  inputRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  messageInput: {
    flex: 1,
    backgroundColor: 'hsl(220, 15%, 22%)', // --input
    borderRadius: 6, // --radius
    padding: 12,
    fontSize: 14,
    color: 'hsl(210, 40%, 98%)', // --foreground
    minHeight: 40,
    borderWidth: 1,
    borderColor: 'hsl(220, 15%, 25%)', // --border
  },
  sendButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'hsl(180, 94%, 29%)', // --primary
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 6, // --radius
    gap: 8,
  },
  sendIcon: {
    fontSize: 16,
  },
  sendButtonText: {
    color: 'hsl(210, 40%, 98%)', // --primary-foreground
    fontSize: 14,
    fontWeight: '600',
  },
  optionsContainer: {
    flexDirection: 'row',
    gap: 16,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  activeOption: {
    // No additional styling needed for active state
  },
  optionText: {
    fontSize: 12,
    color: 'hsl(215, 20%, 65%)', // --muted-foreground
    fontWeight: '500',
  },
  activeOptionText: {
    color: 'hsl(210, 40%, 98%)', // --foreground
  },
  // Group Management Styles
  groupSection: {
    backgroundColor: '#1F2937',
    margin: 16,
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
  // Member Management Styles
  memberSection: {
    marginBottom: 16,
  },
  memberSectionTitle: {
    color: '#F9FAFB',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  addMemberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  memberInput: {
    flex: 1,
    marginBottom: 0,
    marginRight: 8,
  },
  addMemberButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'hsl(142, 76%, 36%)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addMemberButtonText: {
    color: '#F9FAFB',
    fontSize: 18,
    fontWeight: '600',
  },
  membersList: {
    marginTop: 8,
  },
  membersListTitle: {
    color: '#9CA3AF',
    fontSize: 12,
    marginBottom: 8,
  },
  memberItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#111827',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    marginBottom: 4,
  },
  memberId: {
    color: '#F9FAFB',
    fontSize: 14,
  },
  removeMemberButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeMemberButtonText: {
    color: '#F9FAFB',
    fontSize: 16,
    fontWeight: '600',
  },
  // Channel Actions Styles
  channelActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  channelDeleteButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    opacity: 0.8,
  },
  channelDeleteButtonText: {
    color: '#EF4444',
    fontSize: 20,
    fontWeight: '300',
  },
  // Delete Confirmation Styles
  deleteConfirmText: {
    color: '#9CA3AF',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  deleteConfirmButton: {
    backgroundColor: '#EF4444',
  },
  deleteConfirmButtonText: {
    color: '#F9FAFB',
    fontSize: 14,
    fontWeight: '600',
  },
  deleteWarningText: {
    color: '#F9FAFB',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
    marginTop: 16,
  },
  deleteConfirmInput: {
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#F9FAFB',
    fontSize: 14,
    marginBottom: 20,
  },
  disabledButton: {
    backgroundColor: '#6B7280',
    opacity: 0.5,
  },
  disabledButtonText: {
    color: '#9CA3AF',
  },
  // Chat Header Right Section
  chatHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerDeleteButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
    opacity: 0.8,
  },
  headerDeleteButtonText: {
    color: '#EF4444',
    fontSize: 16,
    fontWeight: '300',
  }
});
