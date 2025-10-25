// src/services/messageService.ts
// Production-ready message service for QShield

import { encryptAndSendHybrid, fetchAndDecryptHybrid } from './cryptoService';
import keyManager from './keyManager';
import api from '../api';

export interface SecureMessage {
  id: string;
  senderId: string;
  recipientId: string;
  content: string;
  timestamp: number;
  ttl: number;
  encrypted: boolean;
  decrypted: boolean;
  metadata?: any;
}

export interface MessageStatus {
  id: string;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'expired' | 'failed';
  timestamp: number;
  error?: string;
}

class MessageService {
  private static instance: MessageService;
  private messageCache: Map<string, SecureMessage> = new Map();
  private statusCallbacks: Map<string, (status: MessageStatus) => void> = new Map();

  static getInstance(): MessageService {
    if (!MessageService.instance) {
      MessageService.instance = new MessageService();
    }
    return MessageService.instance;
  }

  /**
   * Send encrypted message
   */
  async sendMessage(
    recipientId: string, 
    content: string, 
    options: {
      ttl?: number;
      metadata?: any;
      onStatus?: (status: MessageStatus) => void;
    } = {}
  ): Promise<SecureMessage> {
    try {
      const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Create message object
      const message: SecureMessage = {
        id: messageId,
        senderId: 'current_user', // TODO: Get from auth service
        recipientId,
        content,
        timestamp: Date.now(),
        ttl: options.ttl || 90, // 90 seconds default
        encrypted: false,
        decrypted: false,
        metadata: options.metadata
      };

      // Store in cache
      this.messageCache.set(messageId, message);

      // Set up status callback
      if (options.onStatus) {
        this.statusCallbacks.set(messageId, options.onStatus);
      }

      // Encrypt and send
      const result = await encryptAndSendHybrid(content, recipientId, {
        ttl_seconds: options.ttl,
        metadata: options.metadata
      });

      // Update message status
      message.encrypted = true;
      this.messageCache.set(messageId, message);
      
      // Notify status
      this.notifyStatus(messageId, {
        id: messageId,
        status: 'sent',
        timestamp: Date.now()
      });

      return message;
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Notify error status
      this.notifyStatus(messageId, {
        id: messageId,
        status: 'failed',
        timestamp: Date.now(),
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Fetch and decrypt messages for user
   */
  async fetchMessages(userId: string): Promise<SecureMessage[]> {
    try {
      // Fetch encrypted messages from server
      const response = await api.get(`/messages/${userId}`);
      const encryptedMessages = response.data;

      const decryptedMessages: SecureMessage[] = [];

      for (const encryptedMsg of encryptedMessages) {
        try {
          // Decrypt message
          const decryptedContent = await this.decryptMessage(encryptedMsg);
          
          const message: SecureMessage = {
            id: encryptedMsg.id,
            senderId: encryptedMsg.sender || 'unknown',
            recipientId: userId,
            content: decryptedContent,
            timestamp: encryptedMsg.timestamp,
            ttl: encryptedMsg.ttl_remaining || 90,
            encrypted: true,
            decrypted: true,
            metadata: encryptedMsg.metadata
          };

          decryptedMessages.push(message);
          this.messageCache.set(message.id, message);
        } catch (error) {
          console.error('Failed to decrypt message:', error);
          // Continue with other messages
        }
      }

      return decryptedMessages;
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      throw error;
    }
  }

  /**
   * Decrypt individual message
   */
  private async decryptMessage(encryptedMsg: any): Promise<string> {
    try {
      // Get recipient's private keys
      const privateKeys = await keyManager.getPrivateKeys(encryptedMsg.recipient_id);
      if (!privateKeys) {
        throw new Error('Private keys not available for decryption');
      }

      // Fetch encrypted message data
      const encryptedData = await api.get(`/fetch/${encryptedMsg.token}`);
      
      // Decrypt using hybrid decryption
      const decryptedContent = await fetchAndDecryptHybrid(
        encryptedData.data,
        privateKeys.kyberPrivateKey,
        privateKeys.x25519PrivateKey
      );

      return decryptedContent;
    } catch (error) {
      console.error('Failed to decrypt message:', error);
      throw error;
    }
  }

  /**
   * Mark message as read
   */
  async markAsRead(messageId: string): Promise<void> {
    try {
      const message = this.messageCache.get(messageId);
      if (message) {
        // Update server
        await api.post(`/read/${messageId}`);
        
        // Update local cache
        message.metadata = { ...message.metadata, read: true };
        this.messageCache.set(messageId, message);
      }
    } catch (error) {
      console.error('Failed to mark message as read:', error);
    }
  }

  /**
   * Delete message (self-destruct)
   */
  async deleteMessage(messageId: string): Promise<void> {
    try {
      // Delete from server
      await api.delete(`/messages/${messageId}`);
      
      // Remove from cache
      this.messageCache.delete(messageId);
    } catch (error) {
      console.error('Failed to delete message:', error);
    }
  }

  /**
   * Get message by ID
   */
  getMessage(messageId: string): SecureMessage | null {
    return this.messageCache.get(messageId) || null;
  }

  /**
   * Get all cached messages
   */
  getAllMessages(): SecureMessage[] {
    return Array.from(this.messageCache.values());
  }

  /**
   * Clear message cache
   */
  clearCache(): void {
    this.messageCache.clear();
  }

  /**
   * Notify status change
   */
  private notifyStatus(messageId: string, status: MessageStatus): void {
    const callback = this.statusCallbacks.get(messageId);
    if (callback) {
      callback(status);
    }
  }

  /**
   * Clean up expired messages
   */
  cleanupExpiredMessages(): void {
    const now = Date.now();
    for (const [id, message] of this.messageCache.entries()) {
      if (now - message.timestamp > message.ttl * 1000) {
        this.messageCache.delete(id);
      }
    }
  }
}

export default MessageService.getInstance();