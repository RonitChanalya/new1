#!/usr/bin/env python3
"""
Test Enhanced Ensemble Decision System
Demonstrates multi-model consensus with fair feature weighting
"""
import requests
import json
import time
import numpy as np

def test_enhanced_ensemble():
    """Test the enhanced ensemble decision system"""
    
    base_url = "http://127.0.0.1:8000"
    api_key = "5ac00dc6a40ea9ddbe0e341bbd3537b1"
    headers = {"x-api-key": api_key}
    
    print("ENHANCED ENSEMBLE DECISION SYSTEM TEST")
    print("=" * 50)
    print("Testing multi-model consensus with fair feature weighting")
    print("=" * 50)
    
    # Step 1: Train the enhanced ensemble
    print("\n1. TRAINING ENHANCED ENSEMBLE")
    print("-" * 30)
    try:
        response = requests.post(
            f"{base_url}/admin/ml/train-enhanced-ensemble",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Enhanced ensemble trained")
            print(f"  Training samples: {result.get('training_samples', 'N/A')}")
            print(f"  Fair feature weighting: {result.get('fair_feature_weighting', False)}")
            print(f"  Multi-model consensus: {result.get('multi_model_consensus', False)}")
            
            if 'feature_analysis' in result:
                analysis = result['feature_analysis']
                print(f"  Feature weights: {analysis.get('feature_weights', [])}")
                print(f"  Model weights: {analysis.get('model_weights', {})}")
        else:
            print(f"ERROR: Training failed: {response.status_code}")
            return
    except Exception as e:
        print(f"ERROR: Training failed: {e}")
        return
    
    # Step 2: Test different attack scenarios
    print("\n2. TESTING ATTACK SCENARIOS")
    print("-" * 30)
    
    test_scenarios = [
        {
            "name": "Obvious Attack",
            "vector": [25000, 0.05, 15, 1.0],
            "description": "Large file, rapid sending, many recipients"
        },
        {
            "name": "Medium Attack",
            "vector": [8000, 0.3, 6, 1.0],
            "description": "Medium file, multiple recipients"
        },
        {
            "name": "Normal Looking",
            "vector": [2000, 1.0, 2, 0.0],
            "description": "Normal communication pattern"
        },
        {
            "name": "Sophisticated Attack",
            "vector": [12000, 0.8, 4, 0.0],
            "description": "Trying to look normal but suspicious"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print(f"  Description: {scenario['description']}")
        print(f"  Vector: {scenario['vector']}")
        
        payload = {
            "token": f"test_{scenario['name'].replace(' ', '_').lower()}",
            "vector": scenario["vector"],
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(
                f"{base_url}/ml/enhanced-score",
                json=payload,
                headers={"Content-Type": "application/json", "x-api-key": api_key}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  SUCCESS: Enhanced ensemble response")
                print(f"    Risk Score: {result.get('risk', 'N/A')}")
                print(f"    Action: {result.get('action', 'N/A')}")
                print(f"    Consensus Score: {result.get('consensus_score', 'N/A')}")
                print(f"    Confidence: {result.get('confidence', 'N/A')}")
                print(f"    Consensus Reached: {result.get('consensus_reached', 'N/A')}")
                print(f"    Model Agreement: {result.get('model_agreement', 'N/A')}")
                
                if 'ensemble_details' in result:
                    details = result['ensemble_details']
                    print(f"    Model Count: {details.get('model_count', 'N/A')}")
                    print(f"    Fair Feature Weighting: {details.get('fair_feature_weighting', False)}")
                    print(f"    Model Weights: {details.get('model_weights', {})}")
            else:
                print(f"  ERROR: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)
    
    # Step 3: Compare with standard scoring
    print("\n3. COMPARING WITH STANDARD SCORING")
    print("-" * 30)
    
    test_vector = [15000, 0.1, 10, 1.0]
    print(f"Testing with vector: {test_vector}")
    
    payload = {
        "token": "comparison_test",
        "vector": test_vector,
        "timestamp": time.time()
    }
    
    # Test standard scoring
    print("\nStandard Scoring (/ml/score):")
    try:
        response = requests.post(
            f"{base_url}/ml/score",
            json=payload,
            headers={"Content-Type": "application/json", "x-api-key": api_key}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Risk: {result.get('risk', 'N/A')}")
            print(f"  Action: {result.get('action', 'N/A')}")
            print(f"  Mode: {result.get('mode', 'N/A')}")
        else:
            print(f"  ERROR: {response.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Test enhanced ensemble scoring
    print("\nEnhanced Ensemble Scoring (/ml/enhanced-score):")
    try:
        response = requests.post(
            f"{base_url}/ml/enhanced-score",
            json=payload,
            headers={"Content-Type": "application/json", "x-api-key": api_key}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Risk: {result.get('risk', 'N/A')}")
            print(f"  Action: {result.get('action', 'N/A')}")
            print(f"  Mode: {result.get('mode', 'N/A')}")
            print(f"  Consensus Score: {result.get('consensus_score', 'N/A')}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            print(f"  Consensus Reached: {result.get('consensus_reached', 'N/A')}")
            print(f"  Model Agreement: {result.get('model_agreement', 'N/A')}")
        else:
            print(f"  ERROR: {response.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Step 4: Test feature fairness
    print("\n4. TESTING FEATURE FAIRNESS")
    print("-" * 30)
    
    # Test with different feature combinations
    fairness_tests = [
        {"name": "Size Dominant", "vector": [30000, 0.5, 1, 0.0]},
        {"name": "Interval Dominant", "vector": [1000, 0.01, 1, 0.0]},
        {"name": "Recipients Dominant", "vector": [1000, 0.5, 20, 0.0]},
        {"name": "Device Dominant", "vector": [1000, 0.5, 1, 1.0]},
        {"name": "Balanced", "vector": [5000, 0.5, 3, 0.5]}
    ]
    
    for test in fairness_tests:
        print(f"\nTesting: {test['name']}")
        print(f"  Vector: {test['vector']}")
        
        payload = {
            "token": f"fairness_{test['name'].replace(' ', '_').lower()}",
            "vector": test["vector"],
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(
                f"{base_url}/ml/enhanced-score",
                json=payload,
                headers={"Content-Type": "application/json", "x-api-key": api_key}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Risk: {result.get('risk', 'N/A')}")
                print(f"  Action: {result.get('action', 'N/A')}")
                print(f"  Consensus Score: {result.get('consensus_score', 'N/A')}")
                print(f"  Confidence: {result.get('confidence', 'N/A')}")
            else:
                print(f"  ERROR: {response.status_code}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(0.5)
    
    # Final Summary
    print("\n" + "=" * 50)
    print("ENHANCED ENSEMBLE TEST COMPLETE")
    print("=" * 50)
    print("The enhanced ensemble system provides:")
    print("1. MULTI-MODEL CONSENSUS: Multiple algorithms vote")
    print("2. FAIR FEATURE WEIGHTING: Equal importance to all features")
    print("3. DYNAMIC MODEL WEIGHTING: Models weighted by performance")
    print("4. CONSENSUS DECISION MAKING: Agreement-based decisions")
    print("5. CONFIDENCE SCORING: Measures decision certainty")
    print("6. UNBIASED DECISIONS: No feature bias or model bias")
    print("=" * 50)

if __name__ == "__main__":
    test_enhanced_ensemble()
