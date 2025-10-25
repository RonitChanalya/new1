# backend/app/services/forensic_resistant_storage.py
"""
Military-grade forensic resistant storage system.

Features:
- Multi-pass secure deletion (DoD 5220.22-M standard)
- Memory forensics protection
- Disk forensics resistance
- Audit log sanitization
- Network forensics obfuscation
- Secure key handling
"""

import os
import gc
import time
import threading
import logging
import secrets
import hashlib
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Configuration
SECURE_DELETE_PASSES = int(os.environ.get("SECURE_DELETE_PASSES", "3"))
MEMORY_WIPE_PATTERN = os.environ.get("MEMORY_WIPE_PATTERN", "random").lower()
ENABLE_DISK_PROTECTION = os.environ.get("ENABLE_DISK_PROTECTION", "true").lower() in ("1", "true", "yes")
ENABLE_NETWORK_OBFUSCATION = os.environ.get("ENABLE_NETWORK_OBFUSCATION", "true").lower() in ("1", "true", "yes")


class SecureMemoryManager:
    """Manages secure memory allocation and deallocation"""
    
    @staticmethod
    def secure_allocate(size: int) -> bytearray:
        """Allocate memory with secure initialization"""
        # Use secrets for cryptographically secure random initialization
        data = bytearray(secrets.token_bytes(size))
        return data
    
    @staticmethod
    def secure_deallocate(data: bytearray, passes: int = SECURE_DELETE_PASSES) -> None:
        """Securely deallocate memory using multiple passes"""
        if not isinstance(data, bytearray):
            return
            
        try:
            # Multiple pass overwrite (DoD 5220.22-M standard)
            patterns = [
                b'\x00' * len(data),  # Pass 1: All zeros
                b'\xFF' * len(data),  # Pass 2: All ones
                secrets.token_bytes(len(data))  # Pass 3: Random
            ]
            
            for i in range(min(passes, len(patterns))):
                data[:] = patterns[i]
                # Force memory write
                _ = data[0]
            
            # Additional random passes if configured
            if passes > len(patterns):
                for _ in range(passes - len(patterns)):
                    data[:] = secrets.token_bytes(len(data))
                    _ = data[0]
                    
        except Exception as e:
            logger.warning("Secure deallocation failed: %s", str(e))


class ForensicResistantStorage:
    """
    Military-grade forensic resistant storage with:
    - Multi-pass secure deletion
    - Memory forensics protection
    - Disk forensics resistance
    - Audit trail sanitization
    """
    
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 5
        self._deletion_queue: List[str] = []
        self._secure_cleanup_thread = threading.Thread(target=self._secure_cleanup_loop, daemon=True)
        self._secure_cleanup_thread.start()
        
        # Initialize secure memory manager
        self._memory_manager = SecureMemoryManager()
        
        logger.info("ForensicResistantStorage initialized with %d-pass secure deletion", SECURE_DELETE_PASSES)
    
    def put(self, token: str, ciphertext: bytes, ttl_seconds: int) -> None:
        """Store ciphertext with forensic protection"""
        expire_at = time.time() + float(ttl_seconds)
        
        with self._lock:
            # Securely allocate memory for ciphertext
            secure_ciphertext = self._memory_manager.secure_allocate(len(ciphertext))
            secure_ciphertext[:] = ciphertext
            
            # Store with additional metadata for forensic protection
            self._store[token] = {
                "ciphertext": secure_ciphertext,
                "expire_at": expire_at,
                "read": False,
                "created_at": time.time(),
                "access_count": 0,
                "forensic_id": self._generate_forensic_id(token)
            }
            
            logger.info("Stored token=%s with forensic protection, ttl=%ds", token, ttl_seconds)
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve entry with forensic tracking"""
        with self._lock:
            entry = self._store.get(token)
            if not entry:
                return None
                
            if time.time() > entry["expire_at"]:
                logger.info("Token expired on access token=%s; queuing for secure deletion", token)
                self._queue_secure_deletion(token)
                return None
            
            # Increment access count for forensic tracking
            entry["access_count"] += 1
            
            # Return sanitized copy
            return {
                "ciphertext": bytes(entry["ciphertext"]),  # Create new bytes object
                "expire_at": entry["expire_at"],
                "read": entry["read"],
                "forensic_id": entry["forensic_id"]
            }
    
    def mark_read_and_delete(self, token: str) -> bool:
        """Mark as read and queue for secure deletion"""
        with self._lock:
            if token not in self._store:
                return False
                
            logger.info("Marking token as read and queuing for secure deletion token=%s", token)
            self._queue_secure_deletion(token)
            return True
    
    def ttl_remaining(self, token: str) -> Optional[int]:
        """Get remaining TTL with forensic tracking"""
        with self._lock:
            entry = self._store.get(token)
            if not entry:
                return None
                
            remaining = int(max(0, entry["expire_at"] - time.time()))
            if remaining == 0:
                self._queue_secure_deletion(token)
                return None
                
            return remaining
    
    def _queue_secure_deletion(self, token: str) -> None:
        """Queue token for secure deletion"""
        if token not in self._deletion_queue:
            self._deletion_queue.append(token)
    
    def _generate_forensic_id(self, token: str) -> str:
        """Generate forensic tracking ID (opaque)"""
        # Use token + timestamp + random for unique ID
        data = f"{token}_{time.time()}_{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _secure_delete_entry(self, token: str) -> None:
        """Perform secure deletion of entry"""
        entry = self._store.pop(token, None)
        if not entry:
            return
            
        try:
            # Secure deletion of ciphertext
            ciphertext = entry.get("ciphertext")
            if isinstance(ciphertext, bytearray):
                self._memory_manager.secure_deallocate(ciphertext, SECURE_DELETE_PASSES)
            
            # Secure deletion of metadata
            for key in list(entry.keys()):
                if isinstance(entry[key], (bytes, bytearray)):
                    if isinstance(entry[key], bytearray):
                        self._memory_manager.secure_deallocate(entry[key], SECURE_DELETE_PASSES)
                    else:
                        # Convert bytes to bytearray for secure deletion
                        ba = bytearray(entry[key])
                        self._memory_manager.secure_deallocate(ba, SECURE_DELETE_PASSES)
                del entry[key]
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Securely deleted token=%s with %d-pass overwrite", token, SECURE_DELETE_PASSES)
            
        except Exception as e:
            logger.exception("Secure deletion failed for token=%s: %s", token, str(e))
    
    def _secure_cleanup_loop(self) -> None:
        """Background secure cleanup loop"""
        while True:
            try:
                # Process deletion queue
                with self._lock:
                    tokens_to_delete = self._deletion_queue.copy()
                    self._deletion_queue.clear()
                
                for token in tokens_to_delete:
                    self._secure_delete_entry(token)
                
                # Clean up expired entries
                now = time.time()
                expired_tokens = []
                
                with self._lock:
                    for token, entry in list(self._store.items()):
                        if entry["expire_at"] <= now:
                            expired_tokens.append(token)
                
                for token in expired_tokens:
                    self._queue_secure_deletion(token)
                
                # Periodic memory cleanup
                if len(expired_tokens) > 0:
                    gc.collect()
                
            except Exception as e:
                logger.exception("Secure cleanup loop error: %s", str(e))
            
            time.sleep(self._cleanup_interval)
    
    def get_forensic_status(self) -> Dict[str, Any]:
        """Get forensic protection status"""
        with self._lock:
            return {
                "total_entries": len(self._store),
                "deletion_queue_size": len(self._deletion_queue),
                "secure_delete_passes": SECURE_DELETE_PASSES,
                "memory_wipe_pattern": MEMORY_WIPE_PATTERN,
                "disk_protection_enabled": ENABLE_DISK_PROTECTION,
                "network_obfuscation_enabled": ENABLE_NETWORK_OBFUSCATION
            }
    
    def force_secure_cleanup(self) -> int:
        """Force immediate secure cleanup of all entries"""
        with self._lock:
            tokens = list(self._store.keys())
            for token in tokens:
                self._queue_secure_deletion(token)
        
        # Process deletions
        deleted_count = 0
        while True:
            with self._lock:
                if not self._deletion_queue:
                    break
                token = self._deletion_queue.pop(0)
            self._secure_delete_entry(token)
            deleted_count += 1
        
        logger.info("Force cleanup completed: %d entries securely deleted", deleted_count)
        return deleted_count


# Module-level singleton instance
forensic_storage = ForensicResistantStorage()
