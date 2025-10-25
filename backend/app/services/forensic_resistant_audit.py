# backend/app/services/forensic_resistant_audit.py
"""
Forensic-resistant audit logging system.

Features:
- No sensitive data in logs
- Opaque identifiers only
- Secure log rotation
- Tamper detection
- Minimal forensic footprint
"""

import os
import time
import json
import hashlib
import logging
import threading
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Configuration
AUDIT_LOG_PATH = os.environ.get("FORENSIC_AUDIT_LOG_PATH", "/var/log/secure_messaging_forensic.log")
AUDIT_LOG_MAX_SIZE = int(os.environ.get("AUDIT_LOG_MAX_SIZE", "10485760"))  # 10MB
AUDIT_LOG_ROTATION_COUNT = int(os.environ.get("AUDIT_LOG_ROTATION_COUNT", "5"))
ENABLE_TAMPER_DETECTION = os.environ.get("ENABLE_TAMPER_DETECTION", "true").lower() in ("1", "true", "yes")


class ForensicResistantAudit:
    """
    Audit logging system designed to resist forensic analysis while maintaining
    security audit trails.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._log_file = None
        self._log_size = 0
        self._tamper_key = self._generate_tamper_key()
        
        # Ensure log directory exists
        log_dir = os.path.dirname(AUDIT_LOG_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        logger.info("ForensicResistantAudit initialized with tamper detection: %s", ENABLE_TAMPER_DETECTION)
    
    def _generate_tamper_key(self) -> bytes:
        """Generate key for tamper detection"""
        # Use system entropy + process ID for uniqueness
        entropy_data = f"{os.getpid()}_{time.time()}_{os.urandom(16)}"
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"forensic_audit_tamper_key"
        ).derive(entropy_data.encode())
    
    def _opaque_hash(self, data: str) -> str:
        """Create opaque hash for identifiers"""
        if not data:
            return "null"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _sanitize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize event data for forensic resistance"""
        sanitized = {
            "ts": int(time.time()),
            "event_id": self._generate_event_id(),
            "event_type": event.get("event_type", "unknown")
        }
        
        # Only include safe fields
        safe_fields = {
            "action", "policy", "risk", "reason", "event_type", 
            "key_id", "ttl", "status", "admin_action"
        }
        
        for key, value in event.items():
            if key in safe_fields:
                sanitized[key] = value
            elif key.endswith("_hash") or key.endswith("_id"):
                # Hash fields are safe
                sanitized[key] = value
            elif key in {"token", "user_id", "client_ip", "device_id"}:
                # Convert sensitive fields to opaque hashes
                sanitized[f"{key}_hash"] = self._opaque_hash(str(value))
        
        return sanitized
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        data = f"{time.time()}_{os.urandom(8)}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate tamper detection checksum"""
        if not ENABLE_TAMPER_DETECTION:
            return ""
        
        # Use HMAC for tamper detection
        hmac = hashlib.pbkdf2_hmac('sha256', data.encode(), self._tamper_key, 1000)
        return hmac.hex()[:16]
    
    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write log entry with tamper detection"""
        try:
            # Convert to JSON
            json_data = json.dumps(entry, separators=(',', ':'), ensure_ascii=False)
            
            # Add tamper detection checksum
            if ENABLE_TAMPER_DETECTION:
                checksum = self._calculate_checksum(json_data)
                json_data = f"{json_data}|{checksum}"
            
            # Write to file
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json_data + "\n")
            
            # Update size tracking
            self._log_size += len(json_data.encode('utf-8'))
            
            # Check for rotation
            if self._log_size > AUDIT_LOG_MAX_SIZE:
                self._rotate_log()
                
        except Exception as e:
            logger.exception("Failed to write audit log entry: %s", str(e))
    
    def _rotate_log(self) -> None:
        """Rotate audit log file"""
        try:
            # Close current log
            if self._log_file:
                self._log_file.close()
                self._log_file = None
            
            # Rotate existing logs
            for i in range(AUDIT_LOG_ROTATION_COUNT - 1, 0, -1):
                old_file = f"{AUDIT_LOG_PATH}.{i}"
                new_file = f"{AUDIT_LOG_PATH}.{i + 1}"
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)
            
            # Move current log to .1
            if os.path.exists(AUDIT_LOG_PATH):
                os.rename(AUDIT_LOG_PATH, f"{AUDIT_LOG_PATH}.1")
            
            # Reset size counter
            self._log_size = 0
            
            logger.info("Audit log rotated successfully")
            
        except Exception as e:
            logger.exception("Log rotation failed: %s", str(e))
    
    def log_message_event(self, event_type: str, **kwargs) -> None:
        """Log message-related event"""
        event = {
            "event_type": event_type,
            **kwargs
        }
        
        sanitized_event = self._sanitize_event(event)
        
        with self._lock:
            self._write_log_entry(sanitized_event)
    
    def log_security_event(self, event_type: str, **kwargs) -> None:
        """Log security-related event"""
        event = {
            "event_type": f"security_{event_type}",
            **kwargs
        }
        
        sanitized_event = self._sanitize_event(event)
        
        with self._lock:
            self._write_log_entry(sanitized_event)
    
    def log_admin_event(self, event_type: str, **kwargs) -> None:
        """Log admin-related event"""
        event = {
            "event_type": f"admin_{event_type}",
            **kwargs
        }
        
        sanitized_event = self._sanitize_event(event)
        
        with self._lock:
            self._write_log_entry(sanitized_event)
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify audit log integrity"""
        if not ENABLE_TAMPER_DETECTION:
            return {"status": "disabled", "message": "Tamper detection disabled"}
        
        try:
            with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            valid_entries = 0
            invalid_entries = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if "|" in line:
                    json_data, checksum = line.rsplit("|", 1)
                    expected_checksum = self._calculate_checksum(json_data)
                    if checksum == expected_checksum:
                        valid_entries += 1
                    else:
                        invalid_entries += 1
                else:
                    # Old format without checksum
                    valid_entries += 1
            
            return {
                "status": "verified" if invalid_entries == 0 else "tampered",
                "valid_entries": valid_entries,
                "invalid_entries": invalid_entries,
                "total_entries": valid_entries + invalid_entries
            }
            
        except Exception as e:
            logger.exception("Log integrity verification failed: %s", str(e))
            return {"status": "error", "message": str(e)}
    
    def get_audit_status(self) -> Dict[str, Any]:
        """Get audit system status"""
        return {
            "log_path": AUDIT_LOG_PATH,
            "log_size": self._log_size,
            "max_size": AUDIT_LOG_MAX_SIZE,
            "rotation_count": AUDIT_LOG_ROTATION_COUNT,
            "tamper_detection": ENABLE_TAMPER_DETECTION,
            "log_exists": os.path.exists(AUDIT_LOG_PATH)
        }


# Module-level singleton instance
forensic_audit = ForensicResistantAudit()
