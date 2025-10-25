# backend/app/services/storage.py
"""
Enhanced Ephemeral in-memory storage with military-grade forensic resistance.

Features:
- Multi-pass secure deletion (DoD 5220.22-M standard)
- Memory forensics protection
- Network forensics obfuscation
- Secure audit logging
- Tamper detection
- Forensic-resistant metadata handling

Public API:
- put(token: str, ciphertext: bytes, ttl_seconds: int) -> None
- get(token: str) -> Optional[dict]  # returns {'ciphertext': bytes, 'expire_at': float, 'read': bool}
- mark_read_and_delete(token: str) -> bool  # True if deleted
- ttl_remaining(token: str) -> Optional[int]  # seconds remaining or None if not found
- storage (module-level instance)
"""

from typing import Optional, Dict, Any
import time
import threading
import logging
import os

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Import forensic protection modules
try:
    from app.services.forensic_resistant_storage import forensic_storage
    from app.services.forensic_resistant_audit import forensic_audit
    from app.services.network_forensics_protection import network_protection
    FORENSIC_PROTECTION_AVAILABLE = True
    logger.info("Forensic protection modules loaded successfully")
except ImportError as e:
    logger.warning("Forensic protection modules not available: %s", str(e))
    FORENSIC_PROTECTION_AVAILABLE = False


def _secure_wipe_bytes(b: bytes) -> None:
    """
    Best-effort attempt to overwrite byte buffer contents before dropping reference.
    Python does not guarantee secure in-memory overwrite, but this helps in-memory
    hygiene for short-lived demo data.
    """
    try:
        # Convert to mutable bytearray and overwrite
        ba = bytearray(b)
        for i in range(len(ba)):
            ba[i] = 0
    except Exception:
        # If anything goes wrong, ignore because this is best-effort only.
        pass


class EphemeralStorage:
    """
    Enhanced ephemeral storage with military-grade forensic resistance.
    
    This class provides a drop-in replacement for the original EphemeralStorage
    but with enhanced forensic protection capabilities.
    """
    
    def __init__(self):
        if FORENSIC_PROTECTION_AVAILABLE:
            # Use forensic-resistant storage
            self._storage = forensic_storage
            self._audit = forensic_audit
            self._network_protection = network_protection
            logger.info("EphemeralStorage initialized with forensic protection")
        else:
            # Fallback to basic storage
            self._storage = None
            self._audit = None
            self._network_protection = None
            self._store: Dict[str, Dict[str, Any]] = {}
            self._lock = threading.Lock()
            self._cleanup_interval = 5
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()
            logger.warning("EphemeralStorage initialized without forensic protection")
    
    def put(self, token: str, ciphertext: bytes, ttl_seconds: int) -> None:
        """Store ciphertext with forensic protection"""
        if FORENSIC_PROTECTION_AVAILABLE:
            # Use forensic-resistant storage
            self._storage.put(token, ciphertext, ttl_seconds)
            
            # Log the event with forensic protection
            self._audit.log_message_event(
                "message_stored",
                token_hash=self._audit._opaque_hash(token),
                ttl=ttl_seconds,
                message_size=len(ciphertext)
            )
        else:
            # Fallback to basic storage
            expire_at = time.time() + float(ttl_seconds)
            with self._lock:
                self._store[token] = {
                    "ciphertext": bytes(ciphertext),
                    "expire_at": expire_at,
                    "read": False,
                }
                logger.info(f"Stored token={token!r}, ttl={ttl_seconds}s, expire_at={expire_at}.")
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve entry with forensic tracking"""
        if FORENSIC_PROTECTION_AVAILABLE:
            # Use forensic-resistant storage
            result = self._storage.get(token)
            
            if result:
                # Log access with forensic protection
                self._audit.log_message_event(
                    "message_accessed",
                    token_hash=self._audit._opaque_hash(token),
                    forensic_id=result.get("forensic_id")
                )
            
            return result
        else:
            # Fallback to basic storage
            with self._lock:
                entry = self._store.get(token)
                if not entry:
                    return None
                if time.time() > entry["expire_at"]:
                    logger.info(f"Token expired on access token={token!r}; removing.")
                    self._delete_internal(token)
                    return None
                return {
                    "ciphertext": entry["ciphertext"],
                    "expire_at": entry["expire_at"],
                    "read": entry["read"],
                }
    
    def mark_read_and_delete(self, token: str) -> bool:
        """Mark as read and delete with forensic protection"""
        if FORENSIC_PROTECTION_AVAILABLE:
            # Use forensic-resistant storage
            result = self._storage.mark_read_and_delete(token)
            
            if result:
                # Log deletion with forensic protection
                self._audit.log_message_event(
                    "message_deleted",
                    token_hash=self._audit._opaque_hash(token),
                    action="read_and_delete"
                )
            
            return result
        else:
            # Fallback to basic storage
            with self._lock:
                if token not in self._store:
                    return False
                logger.info(f"Marking token as read and deleting token={token!r}.")
                self._delete_internal(token)
                return True
    
    def ttl_remaining(self, token: str) -> Optional[int]:
        """Get remaining TTL with forensic tracking"""
        if FORENSIC_PROTECTION_AVAILABLE:
            return self._storage.ttl_remaining(token)
        else:
            # Fallback to basic storage
            with self._lock:
                entry = self._store.get(token)
                if not entry:
                    return None
                remaining = int(max(0, entry["expire_at"] - time.time()))
                if remaining == 0:
                    self._delete_internal(token)
                    return None
                return remaining
    
    def get_forensic_status(self) -> Dict[str, Any]:
        """Get forensic protection status"""
        if FORENSIC_PROTECTION_AVAILABLE:
            return {
                "forensic_protection": True,
                "storage_status": self._storage.get_forensic_status(),
                "audit_status": self._audit.get_audit_status(),
                "network_protection": self._network_protection.get_protection_status()
            }
        else:
            return {
                "forensic_protection": False,
                "message": "Forensic protection modules not available"
            }
    
    def force_secure_cleanup(self) -> int:
        """Force immediate secure cleanup"""
        if FORENSIC_PROTECTION_AVAILABLE:
            deleted_count = self._storage.force_secure_cleanup()
            
            # Log cleanup event
            self._audit.log_admin_event(
                "force_cleanup",
                deleted_count=deleted_count
            )
            
            return deleted_count
        else:
            logger.warning("Force cleanup not available without forensic protection")
            return 0
    
    def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verify audit log integrity"""
        if FORENSIC_PROTECTION_AVAILABLE:
            return self._audit.verify_log_integrity()
        else:
            return {"status": "unavailable", "message": "Audit system not available"}
    
    # Fallback methods for basic storage
    def _delete_internal(self, token: str) -> None:
        """Internal delete helper for basic storage"""
        entry = self._store.pop(token, None)
        if not entry:
            return
        try:
            ciphertext = entry.get("ciphertext")
            if isinstance(ciphertext, (bytes, bytearray)):
                _secure_wipe_bytes(ciphertext)
        except Exception:
            pass
        logger.info(f"Deleted token={token!r} from store.")
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop for basic storage"""
        while True:
            now = time.time()
            to_delete = []
            with self._lock:
                for token, entry in list(self._store.items()):
                    if entry["expire_at"] <= now:
                        to_delete.append(token)
            if to_delete:
                with self._lock:
                    for token in to_delete:
                        logger.info(f"Auto-expire token={token!r}.")
                        self._delete_internal(token)
            time.sleep(self._cleanup_interval)


# Module-level singleton instance (import this in routes)
storage = EphemeralStorage()
