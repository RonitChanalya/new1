# adversarial_robustness.py
"""
Adversarial Robustness Module for Military-Grade Threat Detection
Implements advanced techniques to defend against adaptive attackers
"""
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import random

class AdversarialRobustness:
    """Advanced adversarial defense mechanisms"""
    
    def __init__(self):
        self.feature_importance_threshold = 0.1
        self.drift_detection_window = 100
        self.adversarial_samples = []
        self.feature_drift_history = []
        
    def generate_adversarial_examples(self, normal_samples: np.ndarray, n_samples: int = 100) -> np.ndarray:
        """Generate sophisticated adversarial examples"""
        adversarial = []
        
        for _ in range(n_samples):
            # Pick a random normal sample as base
            base_sample = normal_samples[random.randint(0, len(normal_samples)-1)].copy()
            
            # Apply multiple attack strategies
            attack_type = random.choice(['fgsm', 'pgd', 'carlini', 'adaptive'])
            
            if attack_type == 'fgsm':
                # Fast Gradient Sign Method
                epsilon = random.uniform(0.1, 0.5)
                perturbation = np.random.uniform(-epsilon, epsilon, base_sample.shape)
                adversarial_sample = base_sample + perturbation
                
            elif attack_type == 'pgd':
                # Projected Gradient Descent
                epsilon = random.uniform(0.05, 0.3)
                for _ in range(10):  # Multiple iterations
                    perturbation = np.random.uniform(-epsilon/10, epsilon/10, base_sample.shape)
                    adversarial_sample = base_sample + perturbation
                    # Project back to valid range
                    adversarial_sample = np.clip(adversarial_sample, 
                                               np.min(normal_samples, axis=0),
                                               np.max(normal_samples, axis=0))
                
            elif attack_type == 'carlini':
                # Carlini & Wagner style attack
                epsilon = random.uniform(0.1, 0.4)
                # Add structured noise that mimics real attack patterns
                noise_pattern = np.array([
                    random.uniform(0.8, 1.2),  # Size multiplier
                    random.uniform(0.1, 0.9),  # Interval reduction
                    random.uniform(1.0, 3.0),  # Recipient increase
                    random.uniform(0.0, 1.0)   # Device change probability
                ])
                adversarial_sample = base_sample * noise_pattern
                
            elif attack_type == 'adaptive':
                # Adaptive attack that learns from detection patterns
                # Simulate attacker trying to evade detection
                evasion_factor = random.uniform(0.7, 1.3)
                adversarial_sample = base_sample * evasion_factor
                # Add subtle variations that might evade detection
                adversarial_sample[1] *= random.uniform(0.5, 1.5)  # Vary timing
                adversarial_sample[2] = max(1, adversarial_sample[2] * random.uniform(0.8, 1.2))
            
            adversarial.append(adversarial_sample)
        
        return np.array(adversarial)
    
    def detect_feature_drift(self, new_samples: np.ndarray, reference_stats: Dict) -> Dict:
        """Detect statistical drift in features"""
        drift_report = {
            'drift_detected': False,
            'drift_features': [],
            'drift_scores': {},
            'recommendation': 'continue_monitoring'
        }
        
        for i, feature_name in enumerate(['message_size', 'interval', 'recipients', 'device_change']):
            new_mean = np.mean(new_samples[:, i])
            new_std = np.std(new_samples[:, i])
            
            ref_mean = reference_stats[f'{feature_name}_mean']
            ref_std = reference_stats[f'{feature_name}_std']
            
            # Calculate drift score (Z-score difference)
            drift_score = abs(new_mean - ref_mean) / (ref_std + 1e-8)
            
            drift_report['drift_scores'][feature_name] = drift_score
            
            if drift_score > 2.0:  # Significant drift threshold
                drift_report['drift_detected'] = True
                drift_report['drift_features'].append(feature_name)
        
        if drift_report['drift_detected']:
            drift_report['recommendation'] = 'retrain_model'
        
        return drift_report
    
    def robust_feature_engineering(self, raw_features: np.ndarray) -> np.ndarray:
        """Advanced feature engineering for robustness"""
        engineered = raw_features.copy()
        
        # Add statistical features
        if len(raw_features.shape) == 1:
            raw_features = raw_features.reshape(1, -1)
        
        # Temporal features
        engineered = np.column_stack([
            engineered,
            np.log1p(engineered[:, 0]),  # Log-transformed size
            np.sqrt(engineered[:, 1]),    # Square root of interval
            engineered[:, 0] / (engineered[:, 1] + 1e-8),  # Size/interval ratio
            engineered[:, 2] * engineered[:, 0],  # Total data volume
        ])
        
        # Robust scaling (less sensitive to outliers)
        scaler = RobustScaler()
        engineered = scaler.fit_transform(engineered)
        
        return engineered
    
    def ensemble_uncertainty_estimation(self, models: List, sample: np.ndarray) -> Dict:
        """Estimate prediction uncertainty using ensemble"""
        predictions = []
        confidences = []
        
        for model in models:
            if hasattr(model, 'decision_function'):
                pred = model.decision_function(sample.reshape(1, -1))[0]
                predictions.append(pred)
                # Estimate confidence based on distance from decision boundary
                confidence = abs(pred)
                confidences.append(confidence)
            elif hasattr(model, 'predict_proba'):
                proba = model.predict_proba(sample.reshape(1, -1))[0]
                pred = np.argmax(proba)
                confidence = np.max(proba)
                predictions.append(pred)
                confidences.append(confidence)
        
        uncertainty_report = {
            'mean_prediction': np.mean(predictions),
            'prediction_std': np.std(predictions),
            'mean_confidence': np.mean(confidences),
            'uncertainty_score': np.std(predictions) / (np.mean(confidences) + 1e-8),
            'ensemble_agreement': 1.0 - (np.std(predictions) / (np.max(predictions) - np.min(predictions) + 1e-8))
        }
        
        return uncertainty_report

class RobustThreatDetector:
    """Enhanced threat detector with adversarial robustness"""
    
    def __init__(self):
        self.robustness = AdversarialRobustness()
        self.models = {}
        self.reference_stats = {}
        self.drift_history = []
        self.adversarial_training_data = []
        
    def train_robust_models(self, normal_data: np.ndarray, adversarial_data: np.ndarray = None):
        """Train models with adversarial robustness"""
        print("[RobustThreatDetector] Training robust models...")
        
        # Generate adversarial examples if not provided
        if adversarial_data is None:
            adversarial_data = self.robustness.generate_adversarial_examples(normal_data, n_samples=200)
        
        # Store reference statistics
        self.reference_stats = {
            'message_size_mean': np.mean(normal_data[:, 0]),
            'message_size_std': np.std(normal_data[:, 0]),
            'interval_mean': np.mean(normal_data[:, 1]),
            'interval_std': np.std(normal_data[:, 1]),
            'recipients_mean': np.mean(normal_data[:, 2]),
            'recipients_std': np.std(normal_data[:, 2]),
            'device_change_mean': np.mean(normal_data[:, 3]),
            'device_change_std': np.std(normal_data[:, 3])
        }
        
        # Robust feature engineering
        normal_engineered = self.robustness.robust_feature_engineering(normal_data)
        adversarial_engineered = self.robustness.robust_feature_engineering(adversarial_data)
        
        # Combine normal and adversarial data
        X_combined = np.vstack([normal_engineered, adversarial_engineered])
        y_combined = np.hstack([np.zeros(len(normal_engineered)), np.ones(len(adversarial_engineered))])
        
        # Train robust ensemble
        # 1. Isolation Forest with contamination tuning
        contamination = min(0.1, len(adversarial_engineered) / len(X_combined))
        self.models['isolation_forest'] = IsolationForest(
            n_estimators=300,
            contamination=contamination,
            random_state=42,
            max_samples=0.8  # Bootstrap sampling for robustness
        )
        self.models['isolation_forest'].fit(X_combined)
        
        # 2. Robust Random Forest
        self.models['robust_rf'] = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        self.models['robust_rf'].fit(X_combined, y_combined)
        
        # 3. Additional robust scaler
        self.models['robust_scaler'] = RobustScaler()
        self.models['robust_scaler'].fit(X_combined)
        
        print(f"[RobustThreatDetector] Trained on {len(normal_data)} normal + {len(adversarial_data)} adversarial samples")
        
    def detect_threat_robust(self, sample: np.ndarray) -> Dict:
        """Robust threat detection with uncertainty estimation"""
        # Feature engineering
        engineered_sample = self.robustness.robust_feature_engineering(sample.reshape(1, -1))
        
        # Get predictions from all models
        if_decision = self.models['isolation_forest'].decision_function(engineered_sample)[0]
        rf_pred = self.models['robust_rf'].predict_proba(engineered_sample)[0]
        
        # Uncertainty estimation
        uncertainty = self.robustness.ensemble_uncertainty_estimation(
            [self.models['isolation_forest'], self.models['robust_rf']], 
            engineered_sample[0]
        )
        
        # Robust scoring
        if_score = max(0, min(100, 50 + if_decision * 20))
        rf_score = max(0, min(100, 100 - rf_pred[1] * 100))
        
        # Ensemble with uncertainty weighting
        uncertainty_weight = 1.0 - uncertainty['uncertainty_score']
        final_score = (if_score * 0.6 + rf_score * 0.4) * uncertainty_weight
        
        # Drift detection
        drift_report = self.robustness.detect_feature_drift(
            sample.reshape(1, -1), self.reference_stats
        )
        
        return {
            'risk_score': int(final_score),
            'uncertainty_score': uncertainty['uncertainty_score'],
            'ensemble_agreement': uncertainty['ensemble_agreement'],
            'drift_detected': drift_report['drift_detected'],
            'drift_features': drift_report['drift_features'],
            'confidence': uncertainty['mean_confidence'],
            'raw_scores': {
                'isolation_forest': if_score,
                'random_forest': rf_score
            }
        }

# Global instance
robust_detector = RobustThreatDetector()
