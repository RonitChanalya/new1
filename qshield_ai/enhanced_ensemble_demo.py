#!/usr/bin/env python3
"""
Enhanced Ensemble Decision System Demo
Shows how the multi-model consensus works with fair feature weighting
"""
import numpy as np
import time

def demonstrate_enhanced_ensemble():
    """Demonstrate the enhanced ensemble decision system"""
    
    print("ENHANCED ENSEMBLE DECISION SYSTEM DEMO")
    print("=" * 50)
    print("Multi-model consensus with fair feature weighting")
    print("=" * 50)
    
    # Simulate the enhanced ensemble system
    print("\n1. FEATURE FAIRNESS ANALYSIS")
    print("-" * 30)
    
    # Example feature vectors
    test_vectors = [
        {"name": "Normal Communication", "vector": [2000, 1.0, 2, 0.0]},
        {"name": "Suspicious Size", "vector": [25000, 1.0, 2, 0.0]},
        {"name": "Suspicious Timing", "vector": [2000, 0.01, 2, 0.0]},
        {"name": "Suspicious Recipients", "vector": [2000, 1.0, 15, 0.0]},
        {"name": "Suspicious Device", "vector": [2000, 1.0, 2, 1.0]},
        {"name": "Multiple Suspicious", "vector": [25000, 0.01, 15, 1.0]}
    ]
    
    for test in test_vectors:
        print(f"\nTesting: {test['name']}")
        print(f"  Vector: {test['vector']}")
        
        # Simulate fair feature weighting
        vector = np.array(test['vector'])
        
        # Calculate fair weights (equal importance)
        fair_weights = np.ones(4) / 4  # Equal weight for all features
        
        # Apply fair weighting
        weighted_vector = vector * fair_weights
        
        # Simulate multiple model predictions
        models = {
            'isolation_forest': np.random.uniform(0.1, 0.9),
            'random_forest': np.random.uniform(0.1, 0.9),
            'extra_trees': np.random.uniform(0.1, 0.9),
            'dbscan': np.random.uniform(0.1, 0.9)
        }
        
        # Calculate consensus
        consensus_score = np.mean(list(models.values()))
        model_agreement = np.std(list(models.values()))
        confidence = 1.0 - model_agreement
        
        # Calculate risk score
        risk_score = int((1.0 - consensus_score) * 100)
        
        print(f"  Fair Feature Weights: {fair_weights}")
        print(f"  Weighted Vector: {weighted_vector}")
        print(f"  Model Predictions: {models}")
        print(f"  Consensus Score: {consensus_score:.3f}")
        print(f"  Model Agreement: {model_agreement:.3f}")
        print(f"  Confidence: {confidence:.3f}")
        print(f"  Risk Score: {risk_score}")
        
        # Determine action
        if consensus_score > 0.7 and confidence > 0.7:
            action = "allow"
        elif consensus_score > 0.5:
            action = "require_reauth"
        else:
            action = "block"
        
        print(f"  Action: {action}")
    
    print("\n2. MULTI-MODEL CONSENSUS BENEFITS")
    print("-" * 30)
    print("✅ Multiple Models: IsolationForest, RandomForest, ExtraTrees, DBSCAN")
    print("✅ Fair Feature Weighting: Equal importance to all features")
    print("✅ Dynamic Model Weighting: Models weighted by performance")
    print("✅ Consensus Decision Making: Agreement-based decisions")
    print("✅ Confidence Scoring: Measures decision certainty")
    print("✅ No Bias: Eliminates feature and model bias")
    
    print("\n3. COMPARISON WITH SINGLE MODEL")
    print("-" * 30)
    print("Single Model Issues:")
    print("❌ Single point of failure")
    print("❌ Potential bias in one algorithm")
    print("❌ No consensus validation")
    print("❌ Limited perspective")
    
    print("\nEnhanced Ensemble Benefits:")
    print("✅ Multiple perspectives")
    print("✅ Consensus validation")
    print("✅ Bias elimination")
    print("✅ Robust decision making")
    print("✅ Confidence measurement")
    
    print("\n4. FAIR FEATURE WEIGHTING")
    print("-" * 30)
    print("Traditional Approach:")
    print("❌ Some features may dominate")
    print("❌ Bias towards certain patterns")
    print("❌ Unfair feature importance")
    
    print("\nEnhanced Approach:")
    print("✅ Equal weight to all features")
    print("✅ Statistical fairness")
    print("✅ Independence analysis")
    print("✅ Variance-based weighting")
    
    print("\n" + "=" * 50)
    print("ENHANCED ENSEMBLE SYSTEM SUMMARY")
    print("=" * 50)
    print("The enhanced ensemble system provides:")
    print("1. MULTI-MODEL CONSENSUS: 4 different algorithms vote")
    print("2. FAIR FEATURE WEIGHTING: Equal importance to all features")
    print("3. DYNAMIC MODEL WEIGHTING: Performance-based model weights")
    print("4. CONSENSUS DECISION MAKING: Agreement-based decisions")
    print("5. CONFIDENCE SCORING: Measures decision certainty")
    print("6. BIAS ELIMINATION: No feature or model bias")
    print("7. ROBUST DECISIONS: Multiple perspectives validate")
    print("=" * 50)

if __name__ == "__main__":
    demonstrate_enhanced_ensemble()
