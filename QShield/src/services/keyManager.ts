// src/services/keyManager.ts
// Production-ready key management for QShield

import { generateKyberKeypair } from './cryptoService';
import nacl from 'tweetnacl';
import { bytesToBase64, base64ToBytes } from '../utils/base64';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface UserKeyPair {
  userId: string;
  kyberPublicKey: string;
  kyberPrivateKey: string;
  x25519PublicKey: string;
  x25519PrivateKey: string;
  createdAt: number;
  keyVersion: number;
}

export interface KeyRotation {
  oldKeyId: string;
  newKeyId: string;
  rotationDate: number;
  reason: 'security' | 'expiry' | 'compromise' | 'manual';
}

class KeyManager {
  private static instance: KeyManager;
  private userKeys: Map<string, UserKeyPair> = new Map();
  private keyRotations: KeyRotation[] = [];

  static getInstance(): KeyManager {
    if (!KeyManager.instance) {
      KeyManager.instance = new KeyManager();
    }
    return KeyManager.instance;
  }

  /**
   * Generate new keypair for user
   */
  async generateUserKeyPair(userId: string): Promise<UserKeyPair> {
    try {
      // Generate Kyber keypair
      const kyberKeys = await generateKyberKeypair();
      
      // Generate X25519 keypair
      const x25519Keys = nacl.box.keyPair();
      
      const keyPair: UserKeyPair = {
        userId,
        kyberPublicKey: kyberKeys.publicKey_b64,
        kyberPrivateKey: kyberKeys.privateKey_b64,
        x25519PublicKey: bytesToBase64(x25519Keys.publicKey),
        x25519PrivateKey: bytesToBase64(x25519Keys.secretKey),
        createdAt: Date.now(),
        keyVersion: 1
      };

      // Store in memory
      this.userKeys.set(userId, keyPair);
      
      // Persist to storage
      await this.persistKeys();
      
      return keyPair;
    } catch (error) {
      console.error('Failed to generate user keypair:', error);
      throw new Error('Key generation failed');
    }
  }

  /**
   * Get user keypair
   */
  async getUserKeyPair(userId: string): Promise<UserKeyPair | null> {
    // Check memory first
    if (this.userKeys.has(userId)) {
      return this.userKeys.get(userId)!;
    }

    // Load from storage
    await this.loadKeys();
    return this.userKeys.get(userId) || null;
  }

  /**
   * Rotate user keys (forward secrecy)
   */
  async rotateUserKeys(userId: string, reason: KeyRotation['reason'] = 'security'): Promise<UserKeyPair> {
    const oldKeyPair = await this.getUserKeyPair(userId);
    const newKeyPair = await this.generateUserKeyPair(userId);

    // Record rotation
    const rotation: KeyRotation = {
      oldKeyId: oldKeyPair?.kyberPublicKey || '',
      newKeyId: newKeyPair.kyberPublicKey,
      rotationDate: Date.now(),
      reason
    };

    this.keyRotations.push(rotation);
    await this.persistKeys();

    return newKeyPair;
  }

  /**
   * Check if keys need rotation
   */
  shouldRotateKeys(userId: string): boolean {
    const keyPair = this.userKeys.get(userId);
    if (!keyPair) return false;

    const keyAge = Date.now() - keyPair.createdAt;
    const maxKeyAge = 7 * 24 * 60 * 60 * 1000; // 7 days

    return keyAge > maxKeyAge;
  }

  /**
   * Get public keys for user (for encryption)
   */
  async getPublicKeys(userId: string): Promise<{ kyberPublicKey: string; x25519PublicKey: string } | null> {
    const keyPair = await this.getUserKeyPair(userId);
    if (!keyPair) return null;

    return {
      kyberPublicKey: keyPair.kyberPublicKey,
      x25519PublicKey: keyPair.x25519PublicKey
    };
  }

  /**
   * Get private keys for user (for decryption)
   */
  async getPrivateKeys(userId: string): Promise<{ kyberPrivateKey: string; x25519PrivateKey: string } | null> {
    const keyPair = await this.getUserKeyPair(userId);
    if (!keyPair) return null;

    return {
      kyberPrivateKey: keyPair.kyberPrivateKey,
      x25519PrivateKey: keyPair.x25519PrivateKey
    };
  }

  /**
   * Persist keys to storage
   */
  private async persistKeys(): Promise<void> {
    try {
      const keysData = Array.from(this.userKeys.entries());
      await AsyncStorage.setItem('qshield_user_keys', JSON.stringify(keysData));
      await AsyncStorage.setItem('qshield_key_rotations', JSON.stringify(this.keyRotations));
    } catch (error) {
      console.error('Failed to persist keys:', error);
    }
  }

  /**
   * Load keys from storage
   */
  private async loadKeys(): Promise<void> {
    try {
      const keysData = await AsyncStorage.getItem('qshield_user_keys');
      if (keysData) {
        const keys = JSON.parse(keysData);
        this.userKeys = new Map(keys);
      }

      const rotationsData = await AsyncStorage.getItem('qshield_key_rotations');
      if (rotationsData) {
        this.keyRotations = JSON.parse(rotationsData);
      }
    } catch (error) {
      console.error('Failed to load keys:', error);
    }
  }

  /**
   * Clear all keys (logout)
   */
  async clearAllKeys(): Promise<void> {
    this.userKeys.clear();
    this.keyRotations = [];
    await AsyncStorage.removeItem('qshield_user_keys');
    await AsyncStorage.removeItem('qshield_key_rotations');
  }

  /**
   * Get key statistics
   */
  getKeyStats(): { totalUsers: number; totalRotations: number; oldestKey: number } {
    const totalUsers = this.userKeys.size;
    const totalRotations = this.keyRotations.length;
    const oldestKey = Math.min(...Array.from(this.userKeys.values()).map(k => k.createdAt));

    return { totalUsers, totalRotations, oldestKey };
  }
}

export default KeyManager.getInstance();
