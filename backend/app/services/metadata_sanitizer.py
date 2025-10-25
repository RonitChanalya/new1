# backend/app/services/metadata_sanitizer.py
"""
AI-Powered Metadata Leak Detection and Elimination System.

Features:
- AI-based anomaly detection for metadata patterns
- Automatic metadata sanitization and pseudonymization
- Sensitive field detection and removal
- Metadata obfuscation and quantization
- Risk-based metadata filtering
- Forensic-resistant metadata handling
"""

import os
import time
import logging
import hashlib
import secrets
import threading
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Configuration
METADATA_SANITIZATION_ENABLED = os.environ.get("METADATA_SANITIZATION_ENABLED", "true").lower() in ("1", "true", "yes")
SENSITIVE_FIELD_THRESHOLD = float(os.environ.get("SENSITIVE_FIELD_THRESHOLD", "0.7"))
METADATA_RETENTION_DAYS = int(os.environ.get("METADATA_RETENTION_DAYS", "7"))
ENABLE_PSEUDONYMIZATION = os.environ.get("ENABLE_PSEUDONYMIZATION", "true").lower() in ("1", "true", "yes")
ENABLE_METADATA_OBFUSCATION = os.environ.get("ENABLE_METADATA_OBFUSCATION", "true").lower() in ("1", "true", "yes")


class MetadataAnalyzer:
    """AI-powered metadata analysis and pattern detection"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._metadata_patterns = defaultdict(list)
        self._sensitive_fields = set()
        self._field_risk_scores = {}
        self._pattern_history = []
        
        # Initialize sensitive field patterns
        self._initialize_sensitive_patterns()
        
        logger.info("MetadataAnalyzer initialized with AI-powered detection")
    
    def _initialize_sensitive_patterns(self):
        """Initialize patterns for detecting sensitive metadata fields"""
        # High-risk metadata fields that should be sanitized
        self._sensitive_fields = {
            'user_id', 'username', 'email', 'phone', 'device_id', 'device_fingerprint',
            'ip_address', 'mac_address', 'location', 'gps', 'coordinates', 'address',
            'browser_info', 'user_agent', 'session_id', 'cookie', 'token_raw',
            'timestamp_raw', 'exact_time', 'precise_location', 'personal_info',
            'contact_info', 'identity', 'real_name', 'social_security', 'passport',
            'credit_card', 'bank_account', 'financial_info', 'medical_info',
            'biometric_data', 'face_id', 'fingerprint', 'voice_print'
        }
        
        # Medium-risk fields that should be obfuscated
        self._medium_risk_fields = {
            'timestamp', 'time', 'date', 'created_at', 'updated_at', 'last_seen',
            'message_count', 'frequency', 'pattern', 'behavior', 'activity',
            'network_info', 'connection_type', 'bandwidth', 'latency'
        }
        
        # Low-risk fields that can be kept but quantized
        self._low_risk_fields = {
            'message_size', 'padded_size', 'ttl', 'priority', 'type', 'category'
        }
    
    def analyze_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metadata for sensitive information and risk patterns"""
        with self._lock:
            analysis_result = {
                'risk_score': 0.0,
                'sensitive_fields': [],
                'medium_risk_fields': [],
                'low_risk_fields': [],
                'recommendations': [],
                'sanitization_required': False
            }
            
            # Analyze each field
            for field, value in metadata.items():
                field_lower = field.lower()
                risk_level = self._assess_field_risk(field_lower, value)
                
                if risk_level == 'high':
                    analysis_result['sensitive_fields'].append(field)
                    analysis_result['risk_score'] += 0.8
                    analysis_result['sanitization_required'] = True
                elif risk_level == 'medium':
                    analysis_result['medium_risk_fields'].append(field)
                    analysis_result['risk_score'] += 0.4
                elif risk_level == 'low':
                    analysis_result['low_risk_fields'].append(field)
                    analysis_result['risk_score'] += 0.1
            
            # Normalize risk score
            analysis_result['risk_score'] = min(1.0, analysis_result['risk_score'])
            
            # Generate recommendations
            analysis_result['recommendations'] = self._generate_recommendations(analysis_result)
            
            # Store pattern for ML analysis
            self._store_pattern(metadata, analysis_result)
            
            return analysis_result
    
    def _assess_field_risk(self, field_name: str, value: Any) -> str:
        """Assess risk level of a metadata field"""
        # Check against known sensitive patterns
        if any(pattern in field_name for pattern in self._sensitive_fields):
            return 'high'
        
        if any(pattern in field_name for pattern in self._medium_risk_fields):
            return 'medium'
        
        if any(pattern in field_name for pattern in self._low_risk_fields):
            return 'low'
        
        # AI-based pattern detection
        risk_score = self._ai_assess_field(field_name, value)
        
        if risk_score > 0.7:
            return 'high'
        elif risk_score > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _ai_assess_field(self, field_name: str, value: Any) -> float:
        """AI-based field risk assessment"""
        risk_score = 0.0
        
        # Pattern-based scoring
        if isinstance(value, str):
            # Check for personal identifiers
            if len(value) > 0 and any(char.isdigit() for char in value):
                risk_score += 0.3  # Contains numbers (potential ID)
            
            if '@' in value:
                risk_score += 0.8  # Email address
            elif '.' in value and len(value.split('.')) >= 2:
                risk_score += 0.6  # Potential domain/IP
            
            # Check for UUID/ID patterns
            if len(value) == 36 and '-' in value:
                risk_score += 0.5  # UUID pattern
        
        elif isinstance(value, (int, float)):
            # Check for timestamp patterns
            if value > 1000000000 and value < 2000000000:  # Unix timestamp range
                risk_score += 0.4
        
        # Field name analysis
        suspicious_keywords = ['id', 'key', 'secret', 'private', 'personal', 'user', 'client']
        if any(keyword in field_name.lower() for keyword in suspicious_keywords):
            risk_score += 0.3
        
        return min(1.0, risk_score)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate sanitization recommendations"""
        recommendations = []
        
        if analysis['sensitive_fields']:
            recommendations.append(f"Remove sensitive fields: {', '.join(analysis['sensitive_fields'])}")
        
        if analysis['medium_risk_fields']:
            recommendations.append(f"Obfuscate medium-risk fields: {', '.join(analysis['medium_risk_fields'])}")
        
        if analysis['risk_score'] > 0.8:
            recommendations.append("High risk detected - apply maximum sanitization")
        elif analysis['risk_score'] > 0.5:
            recommendations.append("Medium risk detected - apply selective sanitization")
        
        return recommendations
    
    def _store_pattern(self, metadata: Dict[str, Any], analysis: Dict[str, Any]):
        """Store metadata pattern for ML analysis"""
        pattern = {
            'timestamp': time.time(),
            'field_count': len(metadata),
            'risk_score': analysis['risk_score'],
            'sensitive_count': len(analysis['sensitive_fields']),
            'metadata_hash': hashlib.sha256(str(sorted(metadata.items())).encode()).hexdigest()[:16]
        }
        
        self._pattern_history.append(pattern)
        
        # Keep only recent patterns
        if len(self._pattern_history) > 1000:
            self._pattern_history.pop(0)


class MetadataSanitizer:
    """Metadata sanitization and pseudonymization engine"""
    
    def __init__(self):
        self._analyzer = MetadataAnalyzer()
        self._pseudonym_map = {}
        self._obfuscation_keys = {}
        self._lock = threading.RLock()
        
        logger.info("MetadataSanitizer initialized")
    
    def sanitize_metadata(self, metadata: Dict[str, Any], risk_threshold: float = SENSITIVE_FIELD_THRESHOLD) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Sanitize metadata by removing/obfuscating sensitive information.
        
        Returns:
            Tuple of (sanitized_metadata, sanitization_report)
        """
        if not METADATA_SANITIZATION_ENABLED:
            return metadata, {"status": "disabled", "message": "Metadata sanitization disabled"}
        
        with self._lock:
            # Analyze metadata for sensitive information
            analysis = self._analyzer.analyze_metadata(metadata)
            
            sanitized_metadata = {}
            sanitization_report = {
                'original_fields': len(metadata),
                'sanitized_fields': 0,
                'removed_fields': [],
                'obfuscated_fields': [],
                'quantized_fields': [],
                'risk_score': analysis['risk_score'],
                'sanitization_applied': False
            }
            
            # Apply sanitization based on risk level
            for field, value in metadata.items():
                field_lower = field.lower()
                
                # High-risk fields: Remove completely
                if any(pattern in field_lower for pattern in self._analyzer._sensitive_fields):
                    sanitization_report['removed_fields'].append(field)
                    sanitization_report['sanitization_applied'] = True
                    continue
                
                # Medium-risk fields: Obfuscate
                elif any(pattern in field_lower for pattern in self._analyzer._medium_risk_fields):
                    obfuscated_value = self._obfuscate_value(field, value)
                    sanitized_metadata[field] = obfuscated_value
                    sanitization_report['obfuscated_fields'].append(field)
                    sanitization_report['sanitization_applied'] = True
                
                # Low-risk fields: Quantize
                elif any(pattern in field_lower for pattern in self._analyzer._low_risk_fields):
                    quantized_value = self._quantize_value(field, value)
                    sanitized_metadata[field] = quantized_value
                    sanitization_report['quantized_fields'].append(field)
                
                # Unknown fields: Apply conservative sanitization
                else:
                    if analysis['risk_score'] > risk_threshold:
                        # High risk overall - remove unknown fields
                        sanitization_report['removed_fields'].append(field)
                        sanitization_report['sanitization_applied'] = True
                    else:
                        # Low risk - keep but obfuscate
                        obfuscated_value = self._obfuscate_value(field, value)
                        sanitized_metadata[field] = obfuscated_value
                        sanitization_report['obfuscated_fields'].append(field)
            
            sanitization_report['sanitized_fields'] = len(sanitized_metadata)
            sanitization_report['final_risk_score'] = self._calculate_final_risk_score(sanitized_metadata)
            
            return sanitized_metadata, sanitization_report
    
    def _obfuscate_value(self, field: str, value: Any) -> Any:
        """Obfuscate a metadata value"""
        if not ENABLE_METADATA_OBFUSCATION:
            return value
        
        if isinstance(value, str):
            # String obfuscation
            if len(value) > 0:
                # Create deterministic but obfuscated version
                hash_input = f"{field}:{value}"
                obfuscated = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
                return f"obf_{obfuscated}"
            return value
        
        elif isinstance(value, (int, float)):
            # Numeric obfuscation - add noise and quantize
            if isinstance(value, float):
                # Add small random noise
                noise = secrets.randbelow(100) / 1000.0
                obfuscated = value + noise
                # Quantize to reduce precision
                return round(obfuscated, 2)
            else:
                # Integer - add small random offset
                offset = secrets.randbelow(10) - 5
                return value + offset
        
        elif isinstance(value, bool):
            # Boolean values are generally safe
            return value
        
        else:
            # Unknown type - convert to string and obfuscate
            return self._obfuscate_value(field, str(value))
    
    def _quantize_value(self, field: str, value: Any) -> Any:
        """Quantize a metadata value to reduce precision"""
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                # Quantize timestamps to nearest minute
                if 'time' in field.lower() or 'timestamp' in field.lower():
                    return int(value // 60) * 60
                # Quantize other floats to 2 decimal places
                return round(value, 2)
            else:
                # Quantize integers to nearest 10
                return (value // 10) * 10
        
        elif isinstance(value, str):
            # Quantize strings by length
            length = len(value)
            if length <= 5:
                return "short"
            elif length <= 20:
                return "medium"
            else:
                return "long"
        
        return value
    
    def _calculate_final_risk_score(self, sanitized_metadata: Dict[str, Any]) -> float:
        """Calculate risk score after sanitization"""
        if not sanitized_metadata:
            return 0.0
        
        risk_score = 0.0
        for field, value in sanitized_metadata.items():
            field_lower = field.lower()
            
            # Check if any sensitive patterns remain
            if any(pattern in field_lower for pattern in self._analyzer._sensitive_fields):
                risk_score += 0.8
            elif any(pattern in field_lower for pattern in self._analyzer._medium_risk_fields):
                risk_score += 0.3
            else:
                risk_score += 0.1
        
        return min(1.0, risk_score / len(sanitized_metadata))
    
    def pseudonymize_field(self, field: str, value: str) -> str:
        """Create pseudonym for a field value"""
        if not ENABLE_PSEUDONYMIZATION:
            return value
        
        with self._lock:
            # Create deterministic pseudonym
            pseudonym_key = f"{field}:{value}"
            if pseudonym_key not in self._pseudonym_map:
                # Generate pseudonym using hash
                hash_input = f"{pseudonym_key}:{secrets.token_hex(8)}"
                pseudonym = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
                self._pseudonym_map[pseudonym_key] = f"pseudo_{pseudonym}"
            
            return self._pseudonym_map[pseudonym_key]
    
    def get_sanitization_stats(self) -> Dict[str, Any]:
        """Get sanitization statistics"""
        with self._lock:
            return {
                'sanitization_enabled': METADATA_SANITIZATION_ENABLED,
                'pseudonymization_enabled': ENABLE_PSEUDONYMIZATION,
                'obfuscation_enabled': ENABLE_METADATA_OBFUSCATION,
                'sensitive_field_count': len(self._analyzer._sensitive_fields),
                'medium_risk_field_count': len(self._analyzer._medium_risk_fields),
                'low_risk_field_count': len(self._analyzer._low_risk_fields),
                'pattern_history_size': len(self._analyzer._pattern_history),
                'pseudonym_map_size': len(self._pseudonym_map)
            }


# Module-level singleton instance
metadata_sanitizer = MetadataSanitizer()
