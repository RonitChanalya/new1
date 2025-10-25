# backend/app/services/network_forensics_protection.py
"""
Network forensics protection system.

Features:
- Traffic analysis resistance
- Timing attack prevention
- Message padding strategies
- Network obfuscation
- Metadata protection
"""

import time
import random
import logging
import threading
from typing import Dict, Any, Optional, List
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Configuration
ENABLE_TIMING_PROTECTION = True
ENABLE_TRAFFIC_ANALYSIS_RESISTANCE = True
MIN_PADDING_SIZE = 64  # Minimum padding in bytes
MAX_PADDING_SIZE = 1024  # Maximum padding in bytes
TIMING_JITTER_RANGE = (0.1, 0.5)  # Random delay range in seconds


class NetworkForensicsProtection:
    """
    Network forensics protection system that implements:
    - Traffic analysis resistance
    - Timing attack prevention
    - Message padding strategies
    - Network obfuscation
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._message_history: List[Dict[str, Any]] = []
        self._timing_patterns: Dict[str, float] = {}
        self._padding_strategies = {
            "random": self._random_padding,
            "fixed": self._fixed_padding,
            "adaptive": self._adaptive_padding
        }
        
        logger.info("NetworkForensicsProtection initialized")
    
    def _random_padding(self, message_size: int) -> int:
        """Generate random padding size"""
        return random.randint(MIN_PADDING_SIZE, MAX_PADDING_SIZE)
    
    def _fixed_padding(self, message_size: int) -> int:
        """Generate fixed padding size based on message size"""
        # Pad to next power of 2
        if message_size <= 64:
            return 64 - message_size
        elif message_size <= 128:
            return 128 - message_size
        elif message_size <= 256:
            return 256 - message_size
        elif message_size <= 512:
            return 512 - message_size
        else:
            return 1024 - message_size
    
    def _adaptive_padding(self, message_size: int) -> int:
        """Generate adaptive padding based on traffic patterns"""
        # Analyze recent message sizes to determine optimal padding
        recent_sizes = [entry["size"] for entry in self._message_history[-10:]]
        if recent_sizes:
            avg_size = sum(recent_sizes) / len(recent_sizes)
            # Pad to make message size less distinguishable
            target_size = int(avg_size * random.uniform(0.8, 1.2))
            return max(0, target_size - message_size)
        else:
            return self._random_padding(message_size)
    
    def add_timing_protection(self, base_delay: float = 0.0) -> float:
        """Add timing protection to prevent timing attacks"""
        if not ENABLE_TIMING_PROTECTION:
            return base_delay
        
        # Add random jitter to prevent timing analysis
        jitter = random.uniform(*TIMING_JITTER_RANGE)
        return base_delay + jitter
    
    def pad_message(self, message: bytes, strategy: str = "adaptive") -> bytes:
        """Add padding to message for traffic analysis resistance"""
        if not ENABLE_TRAFFIC_ANALYSIS_RESISTANCE:
            return message
        
        padding_func = self._padding_strategies.get(strategy, self._adaptive_padding)
        padding_size = padding_func(len(message))
        
        if padding_size <= 0:
            return message
        
        # Generate random padding
        padding = bytes(random.randint(0, 255) for _ in range(padding_size))
        
        # Combine message and padding
        padded_message = message + padding
        
        # Record message pattern for analysis
        with self._lock:
            self._message_history.append({
                "timestamp": time.time(),
                "original_size": len(message),
                "padded_size": len(padded_message),
                "strategy": strategy
            })
            
            # Keep only recent history
            if len(self._message_history) > 100:
                self._message_history.pop(0)
        
        return padded_message
    
    def remove_padding(self, padded_message: bytes, original_size: int) -> bytes:
        """Remove padding from message"""
        if len(padded_message) <= original_size:
            return padded_message
        
        return padded_message[:original_size]
    
    def obfuscate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Obfuscate metadata to prevent traffic analysis"""
        obfuscated = {}
        
        # Round timing to prevent precise timing analysis
        if "timestamp" in metadata:
            # Round to nearest 5 seconds
            timestamp = metadata["timestamp"]
            obfuscated["timestamp"] = round(timestamp / 5) * 5
        
        # Quantize sizes to prevent size analysis
        if "message_size" in metadata:
            size = metadata["message_size"]
            # Quantize to 64-byte buckets
            obfuscated["message_size"] = ((size + 31) // 64) * 64
        
        # Add noise to other numeric fields
        for key, value in metadata.items():
            if isinstance(value, (int, float)) and key not in obfuscated:
                # Add small random noise
                noise = random.uniform(-0.1, 0.1)
                obfuscated[key] = value + noise
            elif key not in obfuscated:
                obfuscated[key] = value
        
        return obfuscated
    
    def generate_dummy_traffic(self, count: int = 5) -> List[bytes]:
        """Generate dummy traffic to obfuscate real traffic patterns"""
        dummy_messages = []
        
        for _ in range(count):
            # Generate random message size
            size = random.randint(32, 512)
            dummy_message = bytes(random.randint(0, 255) for _ in range(size))
            
            # Add padding
            padded_dummy = self.pad_message(dummy_message, "random")
            dummy_messages.append(padded_dummy)
        
        return dummy_messages
    
    def analyze_traffic_patterns(self) -> Dict[str, Any]:
        """Analyze traffic patterns for forensics resistance"""
        with self._lock:
            if not self._message_history:
                return {"status": "no_data"}
            
            recent_entries = self._message_history[-20:]
            
            # Calculate statistics
            sizes = [entry["padded_size"] for entry in recent_entries]
            intervals = []
            
            for i in range(1, len(recent_entries)):
                interval = recent_entries[i]["timestamp"] - recent_entries[i-1]["timestamp"]
                intervals.append(interval)
            
            return {
                "status": "analyzed",
                "message_count": len(recent_entries),
                "avg_size": sum(sizes) / len(sizes) if sizes else 0,
                "size_variance": self._calculate_variance(sizes),
                "avg_interval": sum(intervals) / len(intervals) if intervals else 0,
                "interval_variance": self._calculate_variance(intervals),
                "timing_protection": ENABLE_TIMING_PROTECTION,
                "traffic_analysis_resistance": ENABLE_TRAFFIC_ANALYSIS_RESISTANCE
            }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def get_protection_status(self) -> Dict[str, Any]:
        """Get network forensics protection status"""
        return {
            "timing_protection": ENABLE_TIMING_PROTECTION,
            "traffic_analysis_resistance": ENABLE_TRAFFIC_ANALYSIS_RESISTANCE,
            "min_padding_size": MIN_PADDING_SIZE,
            "max_padding_size": MAX_PADDING_SIZE,
            "timing_jitter_range": TIMING_JITTER_RANGE,
            "message_history_size": len(self._message_history),
            "padding_strategies": list(self._padding_strategies.keys())
        }


# Module-level singleton instance
network_protection = NetworkForensicsProtection()
