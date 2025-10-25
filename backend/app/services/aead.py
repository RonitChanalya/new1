# backend/app/services/aead.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from typing import Tuple

# AEAD encrypt/decrypt helpers using AES-GCM (nonce 12 bytes)
# Note: AESGCM requires key lengths 16/24/32 bytes.

def aead_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AEAD key length must be 16, 24, or 32 bytes")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    # return nonce || ciphertext (ciphertext already contains tag appended)
    return nonce + ct

def aead_decrypt(key: bytes, blob: bytes, associated_data: bytes = b"") -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AEAD key length must be 16, 24, or 32 bytes")
    nonce = blob[:12]
    ct = blob[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, associated_data)

def b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def b64_decode(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))
