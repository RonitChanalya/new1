// src/services/cryptoService.ts
// Hybrid encryption (Kyber KEM + X25519) for the frontend (QShield).

import api from '../api';
import sodium from 'libsodium-wrappers';
import nacl from 'tweetnacl';
import { bytesToBase64, base64ToBytes } from '../utils/base64';
import { v4 as uuidv4 } from 'uuid';

// Kyber library (WASM). We use @openpgp/crystals-kyber-js (adapter handles variations)
import * as KyberLib from '@openpgp/crystals-kyber-js';

/* --------------------------------------
   readiness, helpers
   -------------------------------------- */
let kyberReady = false;
let sodiumReady = false;
async function ensureReady() {
  if (!sodiumReady) {
    // libsodium may not have TS types for .ready, cast to any
    await (sodium as any).ready;
    sodiumReady = true;
  }
  if (!kyberReady) {
    // Initialize KyberLib WebAssembly module
    try {
      console.log('Initializing KyberLib WebAssembly...');
      const K: any = KyberLib as any;
      
      // Try different initialization methods
      if (K && typeof K.ready === 'function') {
        console.log('Calling K.ready()...');
        await K.ready();
        console.log('K.ready() completed');
      }
      
      // Try to initialize each MlKem class
      const candidates = ['MlKem768', 'MlKem1024', 'MlKem512'];
      for (const name of candidates) {
        if ((K as any)[name]) {
          const Klass = (K as any)[name];
          console.log(`Initializing ${name}...`);
          
          // Try static initialization methods
          const initMethods = ['ready', 'init', 'setup', '_setup'];
          for (const method of initMethods) {
            if (typeof Klass[method] === 'function') {
              try {
                console.log(`Calling ${name}.${method}()...`);
                const result = Klass[method]();
                if (result && typeof result.then === 'function') {
                  await result;
                }
                console.log(`${name}.${method}() completed`);
                break;
              } catch (e) {
                console.log(`${name}.${method}() failed:`, e);
              }
            }
          }
        }
      }
      
      // Try module-level initialization
      const moduleInitMethods = ['ready', 'init', 'setup', '_setup'];
      for (const method of moduleInitMethods) {
        if (typeof K[method] === 'function') {
          try {
            console.log(`Calling module.${method}()...`);
            const result = K[method]();
            if (result && typeof result.then === 'function') {
              await result;
            }
            console.log(`module.${method}() completed`);
            break;
          } catch (e) {
            console.log(`module.${method}() failed:`, e);
          }
        }
      }
      
    } catch (error) {
      console.log('KyberLib initialization error:', error);
      // Continue anyway - some libs don't need explicit init
    }
    
    // Add a small delay to ensure WebAssembly is fully loaded
    await new Promise(resolve => setTimeout(resolve, 100));
    kyberReady = true;
  }
}

function u8ToB64(u8: Uint8Array) { return bytesToBase64(u8); }
function b64ToU8(b64: string) { return base64ToBytes(b64); }

// Simple 32-byte derive using libsodium generichash (for demo). Replace with HKDF for production.
export function deriveSymmetricKey(sharedA: Uint8Array, sharedB: Uint8Array, info = 'qshield-hybrid') {
  const concat = new Uint8Array(sharedA.length + sharedB.length);
  concat.set(sharedA, 0);
  concat.set(sharedB, sharedA.length);
  return sodium.crypto_generichash(32, concat, sodium.from_string(info));
}

/* --------------------------------------
   Kyber adapter (MlKem classes detection + wrappers)
   -------------------------------------- */

async function pickKemInstance() {
  console.log('Available KyberLib keys:', Object.keys(KyberLib));
  
  // prefer balanced security (768) then 1024 then 512
  const candidates = ['MlKem768', 'MlKem1024', 'MlKem512'];
  let Klass: any = null;
  for (const name of candidates) {
    if ((KyberLib as any)[name]) { 
      Klass = (KyberLib as any)[name]; 
      console.log(`Found class: ${name}`);
      break; 
    }
  }
  if (!Klass) {
    const keys = Object.keys(KyberLib);
    for (const k of keys) {
      if (/MlKem(512|768|1024)/i.test(k)) { 
        Klass = (KyberLib as any)[k]; 
        console.log(`Found class by regex: ${k}`);
        break; 
      }
    }
  }
  if (!Klass) throw new Error('No MlKem class found in KyberLib (check library version)');

  console.log('Found Kyber class:', Klass.name || 'unnamed');
  console.log('Class prototype methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(Klass)));

  // For crystals-kyber-js, the classes might be used statically
  // Let's try using the class directly instead of instantiating
  console.log('Trying to use class statically...');
  
  // Check if the class has static methods we can use directly
  const staticMethods = Object.getOwnPropertyNames(Klass).filter(name => 
    typeof Klass[name] === 'function' && name !== 'constructor'
  );
  console.log('Static methods on class:', staticMethods);
  
  // Return the class itself for static usage
  return Klass;
}

function normalizeKeypairResult(kpRes: any) {
  if (!kpRes) return null;
  if (Array.isArray(kpRes) && kpRes.length >= 2) {
    const pub = kpRes[0] instanceof Uint8Array ? kpRes[0] : (typeof kpRes[0] === 'string' ? b64ToU8(kpRes[0]) : null);
    const priv = kpRes[1] instanceof Uint8Array ? kpRes[1] : (typeof kpRes[1] === 'string' ? b64ToU8(kpRes[1]) : null);
    if (pub && priv) return { pub, priv };
  }
  const maybePubKeys = ['publicKey','public_key','pk','pub','public'];
  const maybePrivKeys = ['privateKey','private_key','sk','priv','secret','private'];
  let pub:any = null, priv:any = null;
  for (const k of maybePubKeys) if (kpRes[k]) pub = kpRes[k];
  for (const k of maybePrivKeys) if (kpRes[k]) priv = kpRes[k];
  if (pub && priv) {
    const pubU8 = pub instanceof Uint8Array ? pub : (typeof pub === 'string' ? b64ToU8(pub) : null);
    const privU8 = priv instanceof Uint8Array ? priv : (typeof priv === 'string' ? b64ToU8(priv) : null);
    if (pubU8 && privU8) return { pub: pubU8, priv: privU8 };
  }
  return null;
}

/**
 * Generate Kyber keypair (returns base64 strings)
 */
// ensure instance is initialized (safety double-check)


export async function generateKyberKeypair() {
  await ensureReady();
  
  // Additional check to ensure WebAssembly is ready
  try {
    console.log('KyberLib keys:', Object.keys(KyberLib));
    
    // Check if the classes are properly loaded
    const candidates = ['MlKem768', 'MlKem1024', 'MlKem512'];
    for (const name of candidates) {
      if ((KyberLib as any)[name]) {
        const Klass = (KyberLib as any)[name];
        console.log(`${name} class found:`, typeof Klass);
        console.log(`${name} methods:`, Object.getOwnPropertyNames(Klass));
      }
    }
  } catch (e) {
    console.log('Error checking KyberLib:', e);
  }
  
  const KemClass = await pickKemInstance();
  console.log('Using KemClass:', KemClass.name || 'unnamed');

  // Try to use the crystals-kyber-js library directly
  try {
    console.log('Attempting direct library usage...');
    
    // Try the documented API for crystals-kyber-js
    if (typeof (KyberLib as any).MlKem768 === 'function') {
      console.log('Trying MlKem768 direct usage...');
      const mlkem = (KyberLib as any).MlKem768;
      
      // Try to create an instance and use it
      try {
        const instance = new mlkem();
        console.log('Created MlKem768 instance');
        
        // Check what methods are available on the instance
        const instanceMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(instance));
        console.log('MlKem768 instance methods:', instanceMethods);
        
        // Try to call key generation methods
        const keygenMethods = ['generateKeyPair', 'keyPair', 'keypair'];
        for (const method of keygenMethods) {
          if (typeof instance[method] === 'function') {
            try {
              console.log(`Trying instance.${method}()...`);
              const result = instance[method]();
              if (result && typeof result.then === 'function') {
                const kpRes = await result;
                const norm = normalizeKeypairResult(kpRes);
                if (norm) {
                  console.log(`Successfully generated keypair using instance.${method}`);
                  return { publicKey_b64: u8ToB64(norm.pub), privateKey_b64: u8ToB64(norm.priv) };
                }
              } else {
                const norm = normalizeKeypairResult(result);
                if (norm) {
                  console.log(`Successfully generated keypair using instance.${method}`);
                  return { publicKey_b64: u8ToB64(norm.pub), privateKey_b64: u8ToB64(norm.priv) };
                }
              }
            } catch (e) {
              console.log(`instance.${method}() failed:`, e);
            }
          }
        }
      } catch (e) {
        console.log('Failed to create MlKem768 instance:', e);
      }
    }
  } catch (e) {
    console.log('Direct library usage failed:', e);
  }

  // Try static methods on the class first
  const keygenCandidates = ['keyPair','keypair','generateKeyPair','generateKeypair','generate','keypairSync','keyPairSync','keygen'];
  for (const name of keygenCandidates) {
    try {
      const fn = (KemClass as any)[name];
      if (typeof fn === 'function') {
        console.log(`Trying static method: ${name}`);
        let kpRes = fn.length === 0 ? fn() : fn();
        if (kpRes && typeof kpRes.then === 'function') kpRes = await kpRes;
        const norm = normalizeKeypairResult(kpRes);
        if (norm) {
          console.log(`Successfully generated keypair using ${name}`);
          return { publicKey_b64: u8ToB64(norm.pub), privateKey_b64: u8ToB64(norm.priv) };
        }
      }
    } catch (e: any) {
      console.log('kyber keygen candidate failed', name, (e as any)?.message ?? e);
    }
  }

  // Try instance methods (create instance first)
  try {
    console.log('Trying to create instance...');
    let instance: any;
    
    // Try different instantiation methods
    try {
      instance = new KemClass();
      console.log('Created instance with new');
    } catch (e1) {
      try {
        instance = KemClass();
        console.log('Created instance with function call');
      } catch (e2) {
        console.log('Failed to create instance:', e2);
        throw new Error('Cannot create KEM instance');
      }
    }

    // Try instance methods
    for (const name of keygenCandidates) {
      try {
        const fn = (instance as any)[name];
        if (typeof fn === 'function') {
          console.log(`Trying instance method: ${name}`);
          let kpRes = fn.length === 0 ? fn() : fn();
          if (kpRes && typeof kpRes.then === 'function') kpRes = await kpRes;
          const norm = normalizeKeypairResult(kpRes);
          if (norm) {
            console.log(`Successfully generated keypair using instance method ${name}`);
            return { publicKey_b64: u8ToB64(norm.pub), privateKey_b64: u8ToB64(norm.priv) };
          }
        }
      } catch (e: any) {
        console.log('kyber instance keygen candidate failed', name, (e as any)?.message ?? e);
      }
    }
  } catch (err) {
    console.log('Instance creation failed:', err);
  }

  // try static methods on module
  const staticNames = ['generateKeyPair','generateKeypair','keypair','keyPair'];
  for (const sName of staticNames) {
    try {
      const fn = (KyberLib as any)[sName];
      if (typeof fn === 'function') {
        console.log(`Trying module static method: ${sName}`);
        let kpRes = fn();
        if (kpRes && typeof kpRes.then === 'function') kpRes = await kpRes;
        const norm = normalizeKeypairResult(kpRes);
        if (norm) {
          console.log(`Successfully generated keypair using module method ${sName}`);
          return { publicKey_b64: u8ToB64(norm.pub), privateKey_b64: u8ToB64(norm.priv) };
        }
      }
    } catch (e) { 
      console.log(`Module method ${sName} failed:`, e);
    }
  }

  // Enhanced error message with debugging info
  const availableKeys = Object.keys(KyberLib);
  const classMethods = KemClass ? Object.getOwnPropertyNames(KemClass) : [];
  const classProtoMethods = KemClass ? Object.getOwnPropertyNames(Object.getPrototypeOf(KemClass)) : [];
  console.log('Available KyberLib keys:', availableKeys);
  console.log('KEM class methods:', classMethods);
  console.log('KEM class prototype methods:', classProtoMethods);
  
  throw new Error(`Kyber keypair API not found. Available KyberLib keys: ${availableKeys.join(', ')}. KEM class methods: ${classMethods.join(', ')}. KEM prototype methods: ${classProtoMethods.join(', ')}. Check library docs for correct method names.`);
}

/**
 * Encapsulate using Kyber adapter: returns { kemCiphertextBytes, kemShared }
 */
export async function kyberEncapsulate(kyberPub_b64: string) {
  await ensureReady();
  const KemClass = await pickKemInstance();
  const kyberPub = b64ToU8(kyberPub_b64);

  console.log('🔧 Kyber encapsulate - using correct API (encap method)');
  console.log('KemClass:', KemClass.name || 'unnamed');

  try {
    // Create instance and use the correct 'encap' method
    const instance = new KemClass();
    console.log('Trying instance.encap with correct API...');
    
    // The correct API is: instance.encap(publicKey) returns [ciphertext, sharedSecret]
    const result = await instance.encap(kyberPub);
    
    if (Array.isArray(result) && result.length >= 2) {
      const kemCiphertextBytes = result[0];
      const kemShared = result[1];
      
      if (kemCiphertextBytes instanceof Uint8Array && kemShared instanceof Uint8Array) {
        console.log('✅ Success with instance.encap - correct API!');
        return { kemCiphertextBytes, kemShared };
      } else {
        console.log('❌ instance.encap returned unexpected types:', typeof kemCiphertextBytes, typeof kemShared);
        throw new Error('encap method returned unexpected result types');
      }
    } else {
      console.log('❌ instance.encap returned unexpected format:', result);
      throw new Error('encap method returned unexpected result format');
    }
  } catch (e) {
    console.error('❌ instance.encap failed:', e);
    throw new Error(`Kyber encapsulation failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
  }
}

/**
 * Decapsulate using Kyber adapter: returns { kemShared }
 */
export async function kyberDecapsulate(kemCipherBytes: Uint8Array, kyberPriv_b64: string) {
  await ensureReady();
  const KemClass = await pickKemInstance();
  const kyberPriv = b64ToU8(kyberPriv_b64);

  console.log('🔧 Kyber decapsulate - using correct API (decap method)');
  console.log('KemClass:', KemClass.name || 'unnamed');

  try {
    // Create instance and use the correct 'decap' method
    const instance = new KemClass();
    console.log('Trying instance.decap with correct API...');
    
    // The correct API is: instance.decap(ciphertext, privateKey)
    const result = await instance.decap(kemCipherBytes, kyberPriv);
    
    if (result instanceof Uint8Array) {
      console.log('✅ Success with instance.decap - correct API!');
      return { kemShared: result };
    } else {
      console.log('❌ instance.decap returned unexpected type:', typeof result);
      throw new Error('decap method returned unexpected result type');
    }
  } catch (e) {
    console.error('❌ instance.decap failed:', e);
    throw new Error(`Kyber decapsulation failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
  }
}

/* --------------------------------------
   High level encrypt/send and fetch/decrypt
   -------------------------------------- */

/**
 * encryptAndSendHybrid: encrypt locally and POST /send
 */
export async function encryptAndSendHybrid(plainText: string, recipientId: string, opts?: { ttl_seconds?: number, metadata?: any }) {
  await ensureReady();

  // 1) ephemeral X25519 keypair
  const eph = nacl.box.keyPair();
  const ephPub = eph.publicKey;
  const ephPriv = eph.secretKey;

  // 2) get recipient kyber pub (and optional x25519 pub)
  const pubResp = await api.get(`/pubkey/${recipientId}`).catch(() => null);
  if (!pubResp || !pubResp.data?.kyber_pub_b64) {
    throw new Error('Recipient Kyber public key not available from server (endpoint /pubkey/{id})');
  }
  const kyberPub_b64 = pubResp.data.kyber_pub_b64;

  // 3) kyber encapsulate (adapter)
  const { kemCiphertextBytes, kemShared } = await kyberEncapsulate(kyberPub_b64);

  // 4) classical ECDH shared if x25519 pub present
  let ecdhShared = new Uint8Array(0);
  if (pubResp.data.x25519_pub_b64) {
    const recipX25519Pub = b64ToU8(pubResp.data.x25519_pub_b64);
    ecdhShared = new Uint8Array(nacl.box.before(recipX25519Pub, ephPriv)); // 32-byte shared key
  }

  // 5) derive symmetric key
  let symKey = ecdhShared.length > 0 ? deriveSymmetricKey(ecdhShared, kemShared) : (sodium as any).crypto_generichash(32, kemShared, (sodium as any).from_string('qshield-only-kyber'));

  console.log('🔧 Encryption debug info:');
  console.log('  - Kyber shared secret length:', kemShared.length);
  console.log('  - ECDH shared secret length:', ecdhShared.length);
  console.log('  - Symmetric key length:', symKey.length);

  // 6) PQC Hybrid AEAD encrypt (XChaCha20-Poly1305)
  // Use the correct libsodium XChaCha20-Poly1305 with proper parameter order
  let nonce = (sodium as any).randombytes_buf((sodium as any).crypto_secretbox_NONCEBYTES); // Use libsodium's nonce size
  console.log('  - Nonce length:', nonce.length);
  console.log('  - Nonce type:', typeof nonce);
  console.log('  - Nonce constructor:', nonce.constructor.name);
  console.log('  - Nonce is Uint8Array:', nonce instanceof Uint8Array);
  console.log('  - Nonce is null/undefined:', nonce === null || nonce === undefined);
  console.log('  - Expected nonce length:', (sodium as any).crypto_secretbox_NONCEBYTES);
  
  // Ensure nonce is a proper Uint8Array
  if (!(nonce instanceof Uint8Array)) {
    console.log('  - Converting nonce to Uint8Array');
    nonce = new Uint8Array(nonce);
  }
  
  // Ensure symKey is a proper Uint8Array
  if (!(symKey instanceof Uint8Array)) {
    console.log('  - Converting symKey to Uint8Array');
    symKey = new Uint8Array(symKey);
  }
  
  console.log('  - Final nonce type:', nonce.constructor.name);
  console.log('  - Final symKey type:', symKey.constructor.name);
  
  // Use secretbox_easy which is more reliable than AEAD
  const cipher = (sodium as any).crypto_secretbox_easy(
    (sodium as any).from_string(plainText), // message
    nonce, // nonce
    symKey // key
  );

  // 7) send to server
  const token = uuidv4();
  const body = {
    token,
    recipient_id: recipientId,
    ciphertext_b64: u8ToB64(cipher),
    nonce_b64: u8ToB64(nonce),
    sender_eph_pub_b64: u8ToB64(ephPub),
    kem_ciphertext_b64: u8ToB64(kemCiphertextBytes),
    original_message: plainText, // Send original message for demo purposes
    ttl_seconds: opts?.ttl_seconds ?? 90, // 90 seconds default
    metadata: opts?.metadata ?? {},
  };

  const res = await api.post('/send', body);
  return { token, serverResponse: res.data };
}

/**
 * fetchAndDecryptHybrid: fetch from server, decapsulate, derive key and decrypt
 */
/**
 * fetchAndDecryptHybrid: fetch from server, decapsulate, derive key and decrypt
 * Replaces the previous implementation to avoid TS errors for possibly-undefined recipient_id.
 */
/**
 * fetchAndDecryptHybrid: fetch from server, decapsulate, derive key and decrypt
 * Safe: narrows data.recipient_id to string before using encodeURIComponent.
 */
export async function fetchAndDecryptHybrid(token: string, recipientPrivateKyber_b64?: string, recipientX25519Priv_b64?: string) {
  await ensureReady();

  const res = await api.get(`/fetch/${token}`);
  const data = res.data;
  const cipher_b64 = data.ciphertext_b64;
  const nonce_b64 = data.nonce_b64;
  const senderEphPub_b64 = data.sender_eph_pub_b64;
  const kemCipher_b64 = data.kem_ciphertext_b64;
  if (!cipher_b64 || !kemCipher_b64) throw new Error('Invalid fetch response');

  const cipher = b64ToU8(cipher_b64);
  const nonce = b64ToU8(nonce_b64);
  const senderEphPub = b64ToU8(senderEphPub_b64);
  const kemCipher = b64ToU8(kemCipher_b64);

  // get recipient private keys (demo endpoint fallback)
  let kyberPriv_b64 = recipientPrivateKyber_b64;
  let x25519Priv_b64 = recipientX25519Priv_b64;
  
  if (!kyberPriv_b64 || !x25519Priv_b64) {
    // Guard & narrow recipient_id into a local `recipientId` that is definitely a string
    const recipientId = data.recipient_id;
    if (!recipientId || typeof recipientId !== 'string') {
      throw new Error('fetch response missing recipient_id');
    }

    // now safe to encode
    const encoded = encodeURIComponent(recipientId);
    const r = await api.get('/me/privkey-demo?id=' + encoded).catch(() => null);
    if (!r || !r.data?.private_key_b64 || !r.data?.x25519_private_b64) {
      throw new Error('Recipient private keys not available');
    }
    kyberPriv_b64 = r.data.private_key_b64;
    x25519Priv_b64 = r.data.x25519_private_b64;
  }

  // decapsulate with Kyber adapter
  if (!kyberPriv_b64 || typeof kyberPriv_b64 !== 'string') {
    throw new Error('No Kyber private key available for decapsulation');
  }
  const { kemShared } = await kyberDecapsulate(kemCipher, kyberPriv_b64);

  // X25519 ECDH computation
  if (!x25519Priv_b64) {
    throw new Error('No X25519 private key available for ECDH');
  }
  const recipPriv = b64ToU8(x25519Priv_b64);
  const ecdhShared = new Uint8Array(nacl.box.before(senderEphPub, recipPriv));

  // derive symmetric key using both Kyber and ECDH shared secrets
  const symKey = deriveSymmetricKey(ecdhShared, kemShared);
  
  console.log('🔧 Decryption debug info:');
  console.log('  - Kyber shared secret length:', kemShared.length);
  console.log('  - ECDH shared secret length:', ecdhShared.length);
  console.log('  - Symmetric key length:', symKey.length);
  console.log('  - Cipher length:', cipher.length);
  console.log('  - Nonce length:', nonce.length);

  // decrypt
  const plainBytes = (sodium as any).crypto_secretbox_open_easy(
    cipher, // ciphertext
    nonce, // nonce
    symKey // key
  );
  if (!plainBytes) throw new Error('Decryption failed');
  const plaintext = (sodium as any).to_string(plainBytes);
  return { plaintext, ttl_remaining: data.ttl_remaining ?? null };
}

