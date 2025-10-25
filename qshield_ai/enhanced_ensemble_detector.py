"""
Enhanced Ensemble Decision System
Multi-model consensus with fair feature weighting and unbiased decision making
"""
import numpy as np
import joblib
import json
import time
from typing import Dict, List, Tuple, Any
from pathlib import Path
from sklearn.ensemble import IsolationForest, RandomForestClassifier, ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
import logging

class EnhancedEnsembleDetector:
    """Enhanced ensemble detector with fair feature weighting and multi-model consensus"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_weights = None
        self.consensus_threshold = 0.6  # 60% of models must agree
        self.model_weights = {}  # Dynamic model weighting based on performance
        self.feature_importance = {}  # Track feature importance across models
        self.decision_history = []  # Track decision patterns for learning
        
        # Initialize multiple decision models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize diverse ensemble of models"""
        self.models = {
            'isolation_forest': IsolationForest(
                n_estimators=200,
                contamination=0.1,
                random_state=42,
                max_samples=0.8,
                max_features=0.8
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=3,
                min_samples_leaf=1,
                random_state=42,
                class_weight='balanced'
            ),
            'extra_trees': ExtraTreesClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=3,
                min_samples_leaf=1,
                random_state=42,
                class_weight='balanced'
            ),
            'dbscan': DBSCAN(
                eps=0.5,
                min_samples=5
            )
        }
        
        # Initialize multiple scalers for different perspectives
        self.scalers = {
            'standard': StandardScaler(),
            'robust': RobustScaler(),
            'minmax': MinMaxScaler(),
            'pca': PCA(n_components=0.95)  # Keep 95% of variance
        }
        
        # Initialize equal feature weights (no bias)
        self.feature_weights = np.ones(4) / 4  # Equal weight for all 4 features
        
    def _normalize_features(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Apply multiple normalization techniques for different perspectives"""
        normalized_features = {}
        
        for name, scaler in self.scalers.items():
            try:
                if name == 'pca':
                    # PCA requires fitted data, use standard scaler first
                    X_std = self.scalers['standard'].fit_transform(X)
                    normalized_features[name] = scaler.fit_transform(X_std)
                else:
                    normalized_features[name] = scaler.fit_transform(X)
            except Exception as e:
                logging.warning(f"Scaler {name} failed: {e}")
                normalized_features[name] = X
                
        return normalized_features
    
    def _calculate_fair_feature_weights(self, X: np.ndarray) -> np.ndarray:
        """Calculate fair feature weights based on statistical properties"""
        # Calculate feature variance (higher variance = more informative)
        feature_variance = np.var(X, axis=0)
        
        # Calculate feature correlation with target (if available)
        # For unsupervised, use feature independence
        feature_independence = []
        for i in range(X.shape[1]):
            # Calculate how independent this feature is from others
            other_features = np.delete(X, i, axis=1)
            correlations = [np.corrcoef(X[:, i], other_features[:, j])[0, 1] 
                          for j in range(other_features.shape[1])]
            independence = 1 - np.mean(np.abs(correlations))
            feature_independence.append(independence)
        
        # Combine variance and independence for fair weighting
        combined_scores = feature_variance * np.array(feature_independence)
        
        # Normalize to sum to 1 (fair distribution)
        if np.sum(combined_scores) > 0:
            fair_weights = combined_scores / np.sum(combined_scores)
        else:
            fair_weights = np.ones(X.shape[1]) / X.shape[1]
            
        return fair_weights
    
    def _apply_fair_feature_weighting(self, X: np.ndarray) -> np.ndarray:
        """Apply fair feature weighting to eliminate bias"""
        # Update feature weights based on current data
        self.feature_weights = self._calculate_fair_feature_weights(X)
        
        # Apply weights to features
        weighted_X = X * self.feature_weights
        
        return weighted_X
    
    def _train_ensemble_models(self, X: np.ndarray, y: np.ndarray = None):
        """Train all ensemble models with different perspectives"""
        # Apply fair feature weighting
        X_weighted = self._apply_fair_feature_weighting(X)
        
        # Get normalized features from different perspectives
        normalized_features = self._normalize_features(X_weighted)
        
        # Train each model with different feature perspectives
        for model_name, model in self.models.items():
            try:
                if model_name == 'isolation_forest':
                    # Use robust scaler for isolation forest
                    X_train = normalized_features.get('robust', X_weighted)
                    model.fit(X_train)
                    
                elif model_name in ['random_forest', 'extra_trees']:
                    # Use standard scaler for supervised models
                    X_train = normalized_features.get('standard', X_weighted)
                    if y is not None:
                        model.fit(X_train, y)
                    else:
                        # Create synthetic labels for unsupervised training
                        synthetic_y = self._create_synthetic_labels(X_train)
                        model.fit(X_train, synthetic_y)
                        
                elif model_name == 'dbscan':
                    # Use PCA for clustering
                    X_train = normalized_features.get('pca', X_weighted)
                    model.fit(X_train)
                    
                # Calculate feature importance for this model
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[model_name] = model.feature_importances_
                elif hasattr(model, 'decision_function'):
                    # For isolation forest, estimate feature importance
                    self.feature_importance[model_name] = self._estimate_feature_importance(model, X_train)
                else:
                    self.feature_importance[model_name] = np.ones(X.shape[1]) / X.shape[1]
                    
            except Exception as e:
                logging.error(f"Failed to train {model_name}: {e}")
                self.feature_importance[model_name] = np.ones(X.shape[1]) / X.shape[1]
    
    def _create_synthetic_labels(self, X: np.ndarray) -> np.ndarray:
        """Create synthetic labels for unsupervised models"""
        # Use clustering to create synthetic labels
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=2, random_state=42)
        labels = kmeans.fit_predict(X)
        return labels
    
    def _estimate_feature_importance(self, model, X: np.ndarray) -> np.ndarray:
        """Estimate feature importance for models without built-in importance"""
        importance = np.zeros(X.shape[1])
        
        for i in range(X.shape[1]):
            # Create perturbed version of feature i
            X_perturbed = X.copy()
            X_perturbed[:, i] = np.random.permutation(X_perturbed[:, i])
            
            # Compare original vs perturbed performance
            try:
                original_score = model.decision_function(X).mean()
                perturbed_score = model.decision_function(X_perturbed).mean()
                importance[i] = abs(original_score - perturbed_score)
            except:
                importance[i] = 1.0 / X.shape[1]
        
        # Normalize importance
        if np.sum(importance) > 0:
            importance = importance / np.sum(importance)
        else:
            importance = np.ones(X.shape[1]) / X.shape[1]
            
        return importance
    
    def _calculate_model_weights(self, X: np.ndarray, y: np.ndarray = None) -> Dict[str, float]:
        """Calculate dynamic model weights based on performance"""
        model_weights = {}
        
        for model_name, model in self.models.items():
            try:
                if model_name == 'isolation_forest':
                    # Use anomaly score consistency
                    scores = model.decision_function(X)
                    weight = 1.0 / (np.std(scores) + 1e-6)  # Lower std = more consistent
                    
                elif model_name in ['random_forest', 'extra_trees']:
                    # Use accuracy if labels available, otherwise use confidence
                    if y is not None:
                        predictions = model.predict(X)
                        weight = np.mean(predictions == y)
                    else:
                        # Use prediction confidence
                        proba = model.predict_proba(X)
                        weight = np.mean(np.max(proba, axis=1))
                        
                elif model_name == 'dbscan':
                    # Use silhouette score
                    labels = model.fit_predict(X)
                    if len(set(labels)) > 1:
                        weight = silhouette_score(X, labels)
                    else:
                        weight = 0.5
                        
                model_weights[model_name] = max(weight, 0.1)  # Minimum weight
                
            except Exception as e:
                logging.warning(f"Failed to calculate weight for {model_name}: {e}")
                model_weights[model_name] = 0.1
                
        # Normalize weights
        total_weight = sum(model_weights.values())
        if total_weight > 0:
            model_weights = {k: v/total_weight for k, v in model_weights.items()}
        else:
            model_weights = {k: 1.0/len(self.models) for k in self.models.keys()}
            
        return model_weights
    
    def _get_model_predictions(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Get predictions from all models"""
        predictions = {}
        
        # Apply fair feature weighting
        X_weighted = self._apply_fair_feature_weighting(X)
        
        # Get normalized features
        normalized_features = self._normalize_features(X_weighted)
        
        for model_name, model in self.models.items():
            try:
                if model_name == 'isolation_forest':
                    X_input = normalized_features.get('robust', X_weighted)
                    scores = model.decision_function(X_input)
                    # Convert to probability (higher = more normal)
                    predictions[model_name] = (scores - scores.min()) / (scores.max() - scores.min() + 1e-6)
                    
                elif model_name in ['random_forest', 'extra_trees']:
                    X_input = normalized_features.get('standard', X_weighted)
                    proba = model.predict_proba(X_input)
                    # Use probability of normal class (index 0)
                    predictions[model_name] = proba[:, 0]
                    
                elif model_name == 'dbscan':
                    X_input = normalized_features.get('pca', X_weighted)
                    labels = model.fit_predict(X_input)
                    # Convert cluster labels to probabilities
                    # Noise points (-1) are more likely to be anomalies
                    proba = np.where(labels == -1, 0.1, 0.9)
                    predictions[model_name] = proba
                    
            except Exception as e:
                logging.warning(f"Failed to get prediction from {model_name}: {e}")
                predictions[model_name] = np.full(X.shape[0], 0.5)  # Neutral prediction
                
        return predictions
    
    def _calculate_consensus_decision(self, predictions: Dict[str, np.ndarray], 
                                   model_weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate consensus decision from all model predictions"""
        # Weighted average of all predictions
        weighted_predictions = np.zeros_like(list(predictions.values())[0])
        
        for model_name, pred in predictions.items():
            weight = model_weights.get(model_name, 0.1)
            weighted_predictions += weight * pred
            
        # Calculate consensus metrics
        consensus_score = np.mean(weighted_predictions)
        model_agreement = np.std(list(predictions.values()))
        confidence = 1.0 - model_agreement  # Lower std = higher confidence
        
        # Determine if consensus is reached
        consensus_reached = model_agreement < 0.3  # Low disagreement = consensus
        
        # Calculate risk score (0-100, higher = more risky)
        risk_score = int((1.0 - consensus_score) * 100)
        risk_score = max(0, min(100, risk_score))
        
        return {
            'risk_score': risk_score,
            'consensus_score': consensus_score,
            'confidence': confidence,
            'consensus_reached': consensus_reached,
            'model_agreement': model_agreement,
            'individual_predictions': predictions,
            'model_weights': model_weights
        }
    
    def train(self, X: np.ndarray, y: np.ndarray = None):
        """Train the enhanced ensemble detector"""
        logging.info(f"Training enhanced ensemble detector with {len(X)} samples")
        
        # Train all models
        self._train_ensemble_models(X, y)
        
        # Calculate model weights based on performance
        self.model_weights = self._calculate_model_weights(X, y)
        
        logging.info(f"Model weights: {self.model_weights}")
        logging.info(f"Feature weights: {self.feature_weights}")
        
    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Make prediction using enhanced ensemble consensus"""
        if not self.models:
            return {
                'risk_score': 50,
                'consensus_score': 0.5,
                'confidence': 0.0,
                'consensus_reached': False,
                'error': 'No models trained'
            }
        
        # Get predictions from all models
        predictions = self._get_model_predictions(X)
        
        # Calculate consensus decision
        result = self._calculate_consensus_decision(predictions, self.model_weights)
        
        # Store decision for learning
        self.decision_history.append({
            'timestamp': time.time(),
            'input': X.tolist() if X.ndim == 1 else X[0].tolist(),
            'result': result
        })
        
        # Keep only recent history
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
            
        return result
    
    def get_feature_analysis(self) -> Dict[str, Any]:
        """Get comprehensive feature analysis"""
        return {
            'feature_weights': self.feature_weights.tolist(),
            'model_weights': self.model_weights,
            'feature_importance': {k: v.tolist() for k, v in self.feature_importance.items()},
            'consensus_threshold': self.consensus_threshold,
            'decision_history_count': len(self.decision_history)
        }
    
    def save_models(self, filepath: str):
        """Save trained models and weights"""
        model_data = {
            'models': {name: model for name, model in self.models.items()},
            'scalers': {name: scaler for name, scaler in self.scalers.items()},
            'feature_weights': self.feature_weights.tolist(),
            'model_weights': self.model_weights,
            'feature_importance': {k: v.tolist() for k, v in self.feature_importance.items()},
            'consensus_threshold': self.consensus_threshold
        }
        
        joblib.dump(model_data, filepath)
        logging.info(f"Enhanced ensemble models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models and weights"""
        try:
            model_data = joblib.load(filepath)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.feature_weights = np.array(model_data['feature_weights'])
            self.model_weights = model_data['model_weights']
            self.feature_importance = {k: np.array(v) for k, v in model_data['feature_importance'].items()}
            self.consensus_threshold = model_data['consensus_threshold']
            
            logging.info(f"Enhanced ensemble models loaded from {filepath}")
            return True
        except Exception as e:
            logging.error(f"Failed to load models: {e}")
            return False

# Global instance
enhanced_detector = EnhancedEnsembleDetector()
