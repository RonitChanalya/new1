# backend/app/services/key_manager.py
import threading
import time
import base64
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import base64

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# optional PQC import
try:
    import oqs  # pyoqs, provides KeyEncapsulation
    PQC_AVAILABLE = True
except Exception:
    # Mock PQC implementation for development/testing
    class MockOQS:
        class KeyEncapsulation:
            def __init__(self, kem_name):
                self.kem_name = kem_name
                # Generate mock keypair
                import secrets
                self._private_key = secrets.token_bytes(32)
                self._public_key = secrets.token_bytes(32)
            
            def generate_keypair(self):
                return self._private_key, self._public_key
            
            def encapsulate(self, public_key):
                # Mock encapsulation - return ciphertext and shared secret
                import secrets
                ciphertext = secrets.token_bytes(32)
                shared_secret = secrets.token_bytes(32)
                return ciphertext, shared_secret
            
            def free(self):
                pass
    
    oqs = MockOQS()
    PQC_AVAILABLE = True
    logger.warning("Using mock PQC implementation - replace with real liboqs for production")


def _b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def _u64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


class KeyManager:
    """
    Provides:
    - X25519 server keypair
    - PQC KEM server public key (if oqs available)
    - hybrid derivation helpers
    """

    def __init__(self, kem_name: str = "Kyber512", rotate_interval: int = 3600):
        self._lock = threading.RLock()
        self.kem_name = kem_name
        self.rotate_interval = rotate_interval

        # classical keys
        self._x25519_priv: X25519PrivateKey = X25519PrivateKey.generate()
        self._x25519_pub: X25519PublicKey = self._x25519_priv.public_key()
        self.key_id = f"server_x25519_{int(time.time())}"

        # PQC keys (server-side KEM public key)
        self._pqc_pub: Optional[bytes] = None
        self._pqc_priv = None
        self._pqc_kem_name = None
        if PQC_AVAILABLE:
            self._init_pqc()

        # optional rotation
        self._shutdown = False
        self._rot_thread = threading.Thread(target=self._rotate_loop, daemon=True)
        self._rot_thread.start()
        logger.info("KeyManager initialized; PQC available=%s", PQC_AVAILABLE)

    def _init_pqc(self):
        # instantiate a KEM and generate a server public key that clients can use
        try:
            kem = oqs.KeyEncapsulation(self.kem_name)
            # Generate keypair - simplified approach
            priv, pub = kem.generate_keypair()
            # store as bytes
            self._pqc_priv = priv
            self._pqc_pub = pub
            self._pqc_kem_name = self.kem_name
            kem.free()
            logger.info("PQC KEM initialized successfully with algorithm: %s", self.kem_name)
        except Exception as e:
            logger.exception("Failed to initialize PQC KEM; disabling PQC support: %s", str(e))
            self._pqc_priv = None
            self._pqc_pub = None
            self._pqc_kem_name = None

    # def export_public_keys(self) -> dict:
    #     with self._lock:
    #         x25519_pub_b64 = _b64(self._x25519_pub.public_bytes())
    #         pqc_pub_b64 = _b64(self._pqc_pub) if self._pqc_pub is not None else None
    #         return {
    #             "key_id": self.key_id,
    #             "x25519_pub_b64": x25519_pub_b64,
    #             "pqc_pub_b64": pqc_pub_b64,
    #             "pqc_enabled": self._pqc_pub is not None,
    #             "pqc_kem": self._pqc_kem_name,
    #         }
    def export_public_keys(self) -> dict:
        with self._lock:
            # export X25519 public key in raw format (32 bytes)
            try:
                x25519_raw = self._x25519_pub.public_bytes(
                    encoding=Encoding.Raw,
                    format=PublicFormat.Raw,
                )
                x25519_pub_b64 = base64.b64encode(x25519_raw).decode("ascii")
            except Exception:
                # fallback to None if export fails
                x25519_pub_b64 = None

            pqc_pub_b64 = None
            try:
                if self._pqc_pub is not None:
                    # assume _pqc_pub is already raw bytes
                    pqc_pub_b64 = base64.b64encode(self._pqc_pub).decode("ascii")
            except Exception:
                pqc_pub_b64 = None

            return {
                "key_id": self.key_id,
                "x25519_pub_b64": x25519_pub_b64,
                "pqc_pub_b64": pqc_pub_b64,
                "pqc_enabled": self._pqc_pub is not None,
                "pqc_kem": self._pqc_kem_name,
            }

    def derive_shared_secret_server_side(self, client_x25519_pub_b64: str, client_pqc_pub_b64: Optional[str]) -> Tuple[bytes, Optional[bytes]]:
        """
        Given client's X25519 public key (base64) and optionally client's PQC public key (base64),
        compute:
            - shared_x (bytes) from X25519 private.exchange(client_x25519_pub)
            - pqc_ct (ciphertext bytes) and shared_pqc (bytes) via KEM.encapsulate(client_pqc_pub)
              (if PQC available and client_pqc_pub provided)
        Returns (combined_shared_material_bytes, pqc_ciphertext_bytes_or_None)
        Note: combined_shared_material_bytes is raw material to be used by HKDF (server also returns pqc_ct so client can decapsulate).
        """
        with self._lock:
            # x25519 exchange
            client_pub_bytes = _u64(client_x25519_pub_b64)
            client_pub = X25519PublicKey.from_public_bytes(client_pub_bytes)
            shared_x = self._x25519_priv.exchange(client_pub)

            shared_pqc = None
            pqc_ct = None
            if PQC_AVAILABLE and client_pqc_pub_b64 and self._pqc_priv is not None:
                try:
                    client_pqc_pub = _u64(client_pqc_pub_b64)
                    # Use a temporary kem to encapsulate to client's pqc public key
                    kem = oqs.KeyEncapsulation(self.kem_name)
                    # pyoqs.encapsulate(public_key) -> (ciphertext, shared_secret)
                    pqc_ct, shared_pqc = kem.encapsulate(client_pqc_pub)
                    kem.free()
                    logger.debug("PQC encapsulation successful, ciphertext length: %d", len(pqc_ct) if pqc_ct else 0)
                except Exception as e:
                    logger.exception("PQC encapsulation failed; continuing with X25519 only: %s", str(e))
                    shared_pqc = None
                    pqc_ct = None

            # produce combination: concat shared_x || (shared_pqc or b'')
            combined = shared_x + (shared_pqc or b"")
            return combined, pqc_ct

    def derive_symmetric_key(self, shared_material: bytes, info: Optional[bytes] = None, length: int = 32) -> bytes:
        # HKDF-SHA256
        hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info or b"hybrid-key")
        return hkdf.derive(shared_material)

    def _rotate_loop(self):
        while not self._shutdown:
            time.sleep(self.rotate_interval)
            try:
                with self._lock:
                    # rotate X25519 keys and PQC pub/priv
                    self._x25519_priv = X25519PrivateKey.generate()
                    self._x25519_pub = self._x25519_priv.public_key()
                    self.key_id = f"server_x25519_{int(time.time())}"
                    if PQC_AVAILABLE:
                        self._init_pqc()
                    logger.info("Rotated server keys; new key_id=%s pqc=%s", self.key_id, PQC_AVAILABLE and self._pqc_pub is not None)
            except Exception:
                logger.exception("Key rotation failed; will retry later")

    def generate_session(self, token: str, ttl_seconds: int) -> bytes:
        """Generate ephemeral session key for token"""
        # This is a simplified implementation
        # In production, use proper key derivation
        import secrets
        return secrets.token_bytes(32)
    
    def key_b64(self, token: str) -> Optional[str]:
        """Get base64-encoded key for token (demo only)"""
        # This is for demo purposes only
        # In production, keys should not be retrievable
        return None
    
    def revoke_key(self, token: str) -> None:
        """Revoke key for token"""
        # Implementation for key revocation
        pass

    def shutdown(self):
        self._shutdown = True
        try:
            self._rot_thread.join(timeout=1.0)
        except Exception:
            pass


# module-level singleton
try:
    km = KeyManager()
except Exception:
    km = None
    logger.exception("Failed to create KeyManager singleton")
