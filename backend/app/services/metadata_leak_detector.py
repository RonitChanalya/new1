# backend/app/services/metadata_leak_detector.py
"""
AI-Powered Metadata Leak Detection System.

Features:
- Integration with existing ML system (IsolationForest)
- Real-time metadata leak detection
- Pattern-based anomaly detection
- Behavioral analysis for metadata patterns
- Risk scoring and classification
- Automatic leak prevention
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Configuration
METADATA_LEAK_DETECTION_ENABLED = os.environ.get("METADATA_LEAK_DETECTION_ENABLED", "true").lower() in ("1", "true", "yes")
LEAK_DETECTION_THRESHOLD = float(os.environ.get("LEAK_DETECTION_THRESHOLD", "0.6"))
ENABLE_BEHAVIORAL_ANALYSIS = os.environ.get("ENABLE_BEHAVIORAL_ANALYSIS", "true").lower() in ("1", "true", "yes")
METADATA_PATTERN_WINDOW = int(os.environ.get("METADATA_PATTERN_WINDOW", "100"))


class MetadataLeakDetector:
    """
    AI-powered metadata leak detection system that integrates with existing ML infrastructure.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._metadata_patterns = []
        self._leak_scores = []
        self._behavioral_patterns = {}
        self._anomaly_threshold = LEAK_DETECTION_THRESHOLD
        
        # Integration with existing ML system
        self._ml_adapter = None
        self._initialize_ml_integration()
        
        logger.info("MetadataLeakDetector initialized with AI-powered detection")
    
    def _initialize_ml_integration(self):
        """Initialize integration with existing ML system"""
        try:
            from app.services import ml_adapter as ml_module
            self._ml_adapter = getattr(ml_module, "ml", None)
            if self._ml_adapter:
                logger.info("ML integration successful - using existing IsolationForest")
            else:
                logger.warning("ML adapter not available - using heuristic detection")
        except Exception as e:
            logger.warning("ML integration failed: %s", str(e))
            self._ml_adapter = None
    
    def detect_metadata_leaks(self, metadata: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect potential metadata leaks using AI-powered analysis.
        
        Args:
            metadata: Metadata to analyze
            context: Additional context (user history, patterns, etc.)
        
        Returns:
            Detection result with risk score and recommendations
        """
        if not METADATA_LEAK_DETECTION_ENABLED:
            return {
                'leak_detected': False,
                'risk_score': 0.0,
                'confidence': 0.0,
                'leak_types': [],
                'recommendations': [],
                'status': 'disabled'
            }
        
        with self._lock:
            detection_result = {
                'leak_detected': False,
                'risk_score': 0.0,
                'confidence': 0.0,
                'leak_types': [],
                'recommendations': [],
                'status': 'analyzed'
            }
            
            # Extract metadata features for ML analysis
            features = self._extract_metadata_features(metadata, context)
            
            # Use ML system for anomaly detection
            if self._ml_adapter:
                ml_score = self._ml_analyze_metadata(features)
                detection_result['risk_score'] = ml_score
                detection_result['confidence'] = 0.8  # High confidence for ML-based detection
            else:
                # Fallback to heuristic analysis
                heuristic_score = self._heuristic_analyze_metadata(metadata, context)
                detection_result['risk_score'] = heuristic_score
                detection_result['confidence'] = 0.6  # Medium confidence for heuristic
            
            # Detect specific leak types
            leak_types = self._detect_leak_types(metadata, features)
            detection_result['leak_types'] = leak_types
            
            # Determine if leak is detected
            detection_result['leak_detected'] = (
                detection_result['risk_score'] > self._anomaly_threshold or
                len(leak_types) > 0
            )
            
            # Generate recommendations
            detection_result['recommendations'] = self._generate_leak_prevention_recommendations(
                leak_types, detection_result['risk_score']
            )
            
            # Store pattern for learning
            self._store_metadata_pattern(metadata, features, detection_result)
            
            return detection_result
    
    def _extract_metadata_features(self, metadata: Dict[str, Any], context: Dict[str, Any] = None) -> List[float]:
        """Extract numerical features from metadata for ML analysis"""
        features = []
        
        # Basic metadata features
        features.append(len(metadata))  # Number of fields
        features.append(sum(1 for v in metadata.values() if isinstance(v, str)))  # String fields
        features.append(sum(1 for v in metadata.values() if isinstance(v, (int, float))))  # Numeric fields
        features.append(sum(1 for v in metadata.values() if isinstance(v, bool)))  # Boolean fields
        
        # Field name analysis
        field_names = [field.lower() for field in metadata.keys()]
        sensitive_keywords = ['id', 'user', 'device', 'ip', 'location', 'personal', 'private']
        sensitive_field_count = sum(1 for field in field_names if any(kw in field for kw in sensitive_keywords))
        features.append(sensitive_field_count)
        
        # Value analysis
        if metadata:
            avg_value_length = np.mean([len(str(v)) for v in metadata.values()])
            features.append(avg_value_length)
            
            # Check for patterns in values
            numeric_values = [v for v in metadata.values() if isinstance(v, (int, float))]
            if numeric_values:
                features.append(np.mean(numeric_values))
                features.append(np.std(numeric_values))
            else:
                features.extend([0.0, 0.0])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # Context features
        if context:
            features.append(context.get('user_message_count', 0))
            features.append(context.get('time_since_last_message', 0))
            features.append(context.get('device_change_count', 0))
        else:
            features.extend([0.0, 0.0, 0.0])
        
        return features
    
    def _ml_analyze_metadata(self, features: List[float]) -> float:
        """Use existing ML system to analyze metadata features"""
        try:
            if self._ml_adapter and hasattr(self._ml_adapter, 'score'):
                # Use existing ML scoring
                ml_score = self._ml_adapter.score(features)
                
                # Convert ML score to leak risk score
                # ML score is typically 0-100, convert to 0-1
                leak_risk = ml_score / 100.0
                
                # Invert if needed (lower ML score = higher risk)
                if leak_risk < 0.5:
                    leak_risk = 1.0 - leak_risk
                
                return leak_risk
            else:
                return 0.5  # Neutral score if ML not available
        except Exception as e:
            logger.exception("ML analysis failed: %s", str(e))
            return 0.5
    
    def _heuristic_analyze_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """Heuristic analysis when ML is not available"""
        risk_score = 0.0
        
        # Field count risk
        field_count = len(metadata)
        if field_count > 10:
            risk_score += 0.3  # Too many fields
        elif field_count > 5:
            risk_score += 0.1
        
        # Sensitive field detection
        sensitive_patterns = [
            'user_id', 'device_id', 'ip_address', 'location', 'gps', 'coordinates',
            'email', 'phone', 'personal', 'private', 'secret', 'password'
        ]
        
        for field, value in metadata.items():
            field_lower = field.lower()
            
            # Check field names
            if any(pattern in field_lower for pattern in sensitive_patterns):
                risk_score += 0.4
            
            # Check values
            if isinstance(value, str):
                if '@' in value:  # Email
                    risk_score += 0.3
                elif len(value) > 50:  # Long strings might contain sensitive data
                    risk_score += 0.2
                elif any(char.isdigit() for char in value) and len(value) > 10:  # Potential ID
                    risk_score += 0.2
        
        # Context-based risk
        if context:
            if context.get('user_message_count', 0) > 100:
                risk_score += 0.1  # High activity user
            if context.get('device_change_count', 0) > 3:
                risk_score += 0.2  # Multiple device changes
        
        return min(1.0, risk_score)
    
    def _detect_leak_types(self, metadata: Dict[str, Any], features: List[float]) -> List[str]:
        """Detect specific types of metadata leaks"""
        leak_types = []
        
        # Identity leak detection
        identity_fields = ['user_id', 'username', 'email', 'name', 'personal_id']
        if any(any(pattern in field.lower() for pattern in identity_fields) for field in metadata.keys()):
            leak_types.append('identity_leak')
        
        # Location leak detection
        location_fields = ['location', 'gps', 'coordinates', 'address', 'city', 'country']
        if any(any(pattern in field.lower() for pattern in location_fields) for field in metadata.keys()):
            leak_types.append('location_leak')
        
        # Device leak detection
        device_fields = ['device_id', 'device_fingerprint', 'mac_address', 'serial_number']
        if any(any(pattern in field.lower() for pattern in device_fields) for field in metadata.keys()):
            leak_types.append('device_leak')
        
        # Network leak detection
        network_fields = ['ip_address', 'network_info', 'connection_type', 'bandwidth']
        if any(any(pattern in field.lower() for pattern in network_fields) for field in metadata.keys()):
            leak_types.append('network_leak')
        
        # Behavioral leak detection
        if ENABLE_BEHAVIORAL_ANALYSIS:
            behavioral_score = self._analyze_behavioral_patterns(metadata, features)
            if behavioral_score > 0.7:
                leak_types.append('behavioral_leak')
        
        # Temporal leak detection
        temporal_fields = ['timestamp', 'exact_time', 'precise_time', 'created_at']
        if any(any(pattern in field.lower() for pattern in temporal_fields) for field in metadata.keys()):
            leak_types.append('temporal_leak')
        
        return leak_types
    
    def _analyze_behavioral_patterns(self, metadata: Dict[str, Any], features: List[float]) -> float:
        """Analyze behavioral patterns for leak detection"""
        behavioral_score = 0.0
        
        # Check for unusual patterns
        if len(metadata) > 15:  # Unusually high metadata count
            behavioral_score += 0.3
        
        # Check for rapid changes in metadata patterns
        if len(self._metadata_patterns) > 10:
            recent_patterns = self._metadata_patterns[-10:]
            pattern_variance = np.var([len(p) for p in recent_patterns])
            if pattern_variance > 5:  # High variance in metadata patterns
                behavioral_score += 0.4
        
        # Check for suspicious field combinations
        suspicious_combinations = [
            ['user_id', 'location'],
            ['device_id', 'ip_address'],
            ['email', 'phone'],
            ['timestamp', 'exact_location']
        ]
        
        field_names = [field.lower() for field in metadata.keys()]
        for combination in suspicious_combinations:
            if all(any(pattern in field for field in field_names) for pattern in combination):
                behavioral_score += 0.5
        
        return min(1.0, behavioral_score)
    
    def _generate_leak_prevention_recommendations(self, leak_types: List[str], risk_score: float) -> List[str]:
        """Generate recommendations for preventing metadata leaks"""
        recommendations = []
        
        if 'identity_leak' in leak_types:
            recommendations.append("Remove or pseudonymize identity-related fields")
        
        if 'location_leak' in leak_types:
            recommendations.append("Remove or obfuscate location information")
        
        if 'device_leak' in leak_types:
            recommendations.append("Remove or hash device identifiers")
        
        if 'network_leak' in leak_types:
            recommendations.append("Remove or obfuscate network information")
        
        if 'behavioral_leak' in leak_types:
            recommendations.append("Apply behavioral pattern obfuscation")
        
        if 'temporal_leak' in leak_types:
            recommendations.append("Quantize timestamps to reduce precision")
        
        if risk_score > 0.8:
            recommendations.append("Apply maximum sanitization - high risk detected")
        elif risk_score > 0.6:
            recommendations.append("Apply selective sanitization - medium risk detected")
        
        return recommendations
    
    def _store_metadata_pattern(self, metadata: Dict[str, Any], features: List[float], detection_result: Dict[str, Any]):
        """Store metadata pattern for learning and analysis"""
        pattern = {
            'timestamp': time.time(),
            'metadata_fields': list(metadata.keys()),
            'features': features,
            'risk_score': detection_result['risk_score'],
            'leak_types': detection_result['leak_types']
        }
        
        self._metadata_patterns.append(pattern)
        
        # Keep only recent patterns
        if len(self._metadata_patterns) > METADATA_PATTERN_WINDOW:
            self._metadata_patterns.pop(0)
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get metadata leak detection statistics"""
        with self._lock:
            if not self._metadata_patterns:
                return {
                    'detection_enabled': METADATA_LEAK_DETECTION_ENABLED,
                    'ml_integration': self._ml_adapter is not None,
                    'pattern_count': 0,
                    'avg_risk_score': 0.0,
                    'leak_types_detected': []
                }
            
            recent_patterns = self._metadata_patterns[-50:]  # Last 50 patterns
            avg_risk_score = np.mean([p['risk_score'] for p in recent_patterns])
            
            # Count leak types
            leak_type_counts = {}
            for pattern in recent_patterns:
                for leak_type in pattern['leak_types']:
                    leak_type_counts[leak_type] = leak_type_counts.get(leak_type, 0) + 1
            
            return {
                'detection_enabled': METADATA_LEAK_DETECTION_ENABLED,
                'ml_integration': self._ml_adapter is not None,
                'pattern_count': len(self._metadata_patterns),
                'avg_risk_score': avg_risk_score,
                'leak_types_detected': leak_type_counts,
                'threshold': self._anomaly_threshold
            }


# Module-level singleton instance
metadata_leak_detector = MetadataLeakDetector()
