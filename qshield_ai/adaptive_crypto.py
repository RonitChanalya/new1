# adaptive_crypto.py
"""
AI-Driven Adaptive Encryption Protocol System
Adapts encryption strength based on real-time threat assessment
"""
import json
import time
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from config import get

class CryptoProtocol(Enum):
    """Available encryption protocols ordered by strength"""
    AES128 = "aes128"           # Standard military grade
    AES256 = "aes256"           # High security
    CHACHA20_POLY1305 = "chacha20_poly1305"  # Modern stream cipher
    HYBRID_PQC_AES256 = "hybrid_pqc_aes256"  # Post-quantum resistant
    HYBRID_PQC_CHACHA20 = "hybrid_pqc_chacha20"  # Post-quantum + modern
    FULL_PQC = "full_pqc"       # Full post-quantum cryptography

@dataclass
class CryptoCapability:
    """Client/server crypto capabilities"""
    protocols: List[CryptoProtocol]
    max_key_size: int
    supports_pqc: bool
    supports_hybrid: bool

@dataclass
class ThreatLevel(Enum):
    """Threat levels that drive crypto adaptation"""
    LOW = "low"           # Standard encryption
    MEDIUM = "medium"     # Enhanced encryption
    HIGH = "high"         # Hybrid encryption
    CRITICAL = "critical" # Full post-quantum

class AdaptiveCryptoManager:
    """AI-driven adaptive encryption protocol manager"""
    
    def __init__(self):
        self.threat_thresholds = {
            "low": 70,      # Risk > 70 = LOW threat
            "medium": 50,   # Risk 50-70 = MEDIUM threat
            "high": 30,     # Risk 30-50 = HIGH threat
            "critical": 30  # Risk < 30 = CRITICAL threat
        }
        
        # Protocol recommendations by threat level
        self.protocol_mapping = {
            "low": CryptoProtocol.AES256,
            "medium": CryptoProtocol.CHACHA20_POLY1305,
            "high": CryptoProtocol.HYBRID_PQC_AES256,
            "critical": CryptoProtocol.FULL_PQC
        }
    
    def assess_threat_level(self, risk_score: int) -> ThreatLevel:
        """Convert AI risk score to threat level"""
        if risk_score >= self.threat_thresholds["low"]:
            return ThreatLevel.LOW
        elif risk_score >= self.threat_thresholds["medium"]:
            return ThreatLevel.MEDIUM
        elif risk_score >= self.threat_thresholds["high"]:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL
    
    def recommend_crypto_protocol(self, risk_score: int, client_capabilities: CryptoCapability) -> Dict:
        """AI-driven crypto protocol recommendation"""
        threat_level = self.assess_threat_level(risk_score)
        recommended_protocol = self.protocol_mapping[threat_level.value]
        
        # Check if client supports recommended protocol
        if recommended_protocol in client_capabilities.protocols:
            selected_protocol = recommended_protocol
        else:
            # Fallback to best available protocol
            selected_protocol = self._find_best_available_protocol(
                threat_level, client_capabilities
            )
        
        return {
            "recommended_protocol": selected_protocol.value,
            "threat_level": threat_level.value,
            "risk_score": risk_score,
            "crypto_strength": self._get_crypto_strength(selected_protocol),
            "pqc_required": threat_level.value in ["high", "critical"],
            "key_rotation_interval": self._get_key_rotation_interval(threat_level),
            "timestamp": time.time()
        }
    
    def _find_best_available_protocol(self, threat_level: ThreatLevel, capabilities: CryptoCapability) -> CryptoProtocol:
        """Find best available protocol based on capabilities"""
        if threat_level.value == "critical" and capabilities.supports_pqc:
            return CryptoProtocol.HYBRID_PQC_AES256
        elif threat_level.value == "high" and capabilities.supports_hybrid:
            return CryptoProtocol.HYBRID_PQC_AES256
        elif CryptoProtocol.CHACHA20_POLY1305 in capabilities.protocols:
            return CryptoProtocol.CHACHA20_POLY1305
        elif CryptoProtocol.AES256 in capabilities.protocols:
            return CryptoProtocol.AES256
        else:
            return CryptoProtocol.AES128
    
    def _get_crypto_strength(self, protocol: CryptoProtocol) -> str:
        """Get human-readable crypto strength"""
        strength_map = {
            CryptoProtocol.AES128: "Standard Military",
            CryptoProtocol.AES256: "High Security",
            CryptoProtocol.CHACHA20_POLY1305: "Modern Stream",
            CryptoProtocol.HYBRID_PQC_AES256: "Post-Quantum Hybrid",
            CryptoProtocol.HYBRID_PQC_CHACHA20: "Post-Quantum Modern",
            CryptoProtocol.FULL_PQC: "Full Post-Quantum"
        }
        return strength_map.get(protocol, "Unknown")
    
    def _get_key_rotation_interval(self, threat_level: ThreatLevel) -> int:
        """Get key rotation interval in seconds based on threat level"""
        intervals = {
            "low": 3600,      # 1 hour
            "medium": 1800,   # 30 minutes
            "high": 600,      # 10 minutes
            "critical": 300   # 5 minutes
        }
        return intervals.get(threat_level.value, 3600)

# Global instance
crypto_manager = AdaptiveCryptoManager()

def get_adaptive_crypto_recommendation(risk_score: int, client_capabilities: Dict) -> Dict:
    """Main function to get AI-driven crypto recommendations"""
    capabilities = CryptoCapability(
        protocols=[CryptoProtocol(p) for p in client_capabilities.get("protocols", ["aes256"])],
        max_key_size=client_capabilities.get("max_key_size", 256),
        supports_pqc=client_capabilities.get("supports_pqc", False),
        supports_hybrid=client_capabilities.get("supports_hybrid", False)
    )
    
    return crypto_manager.recommend_crypto_protocol(risk_score, capabilities)
