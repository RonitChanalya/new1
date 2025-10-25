#!/usr/bin/env python3
"""
Simple Comprehensive Honeypot Test
Tests all honeypot intelligence capabilities without Unicode characters
"""
import requests
import json
import time

def test_honeypot_system():
    """Comprehensive test of honeypot intelligence system"""
    
    base_url = "http://127.0.0.1:8000"
    api_key = "5ac00dc6a40ea9ddbe0e341bbd3537b1"
    headers = {"x-api-key": api_key}
    
    print("COMPREHENSIVE HONEYPOT INTELLIGENCE TEST")
    print("=" * 50)
    
    # Test 1: System Health
    print("\n1. SYSTEM HEALTH CHECK")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("SUCCESS: System is running")
        else:
            print(f"ERROR: System health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"ERROR: System health check failed: {e}")
        return
    
    # Test 2: Deploy Honeypots
    print("\n2. HONEYPOT DEPLOYMENT")
    print("-" * 30)
    honeypot_types = ["fake_ml_endpoint", "fake_crypto_service", "fake_admin_panel"]
    deployed_count = 0
    
    for honeypot_type in honeypot_types:
        try:
            response = requests.post(
                f"{base_url}/admin/honeypot/deploy",
                params={"honeypot_type": honeypot_type},
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: Deployed {honeypot_type}")
                print(f"  ID: {result.get('honeypot_id', 'N/A')}")
                deployed_count += 1
            else:
                print(f"ERROR: Failed to deploy {honeypot_type}")
        except Exception as e:
            print(f"ERROR: Deployment failed for {honeypot_type}: {e}")
    
    print(f"Deployed {deployed_count}/{len(honeypot_types)} honeypots")
    
    # Test 3: Fake ML Endpoint
    print("\n3. FAKE ML ENDPOINT TEST")
    print("-" * 30)
    
    attack_vectors = [
        {"name": "Obvious Attack", "vector": [25000, 0.05, 15, 1.0]},
        {"name": "Medium Attack", "vector": [8000, 0.3, 6, 1.0]},
        {"name": "Normal Looking", "vector": [2000, 1.0, 2, 0.0]}
    ]
    
    for attack in attack_vectors:
        print(f"\nTesting: {attack['name']}")
        print(f"Vector: {attack['vector']}")
        
        payload = {
            "token": f"test_{attack['name'].replace(' ', '_').lower()}",
            "vector": attack["vector"],
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(
                f"{base_url}/ml/fake-score",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: Response received")
                print(f"  Risk Score: {result.get('risk', 'N/A')}")
                print(f"  Action: {result.get('action', 'N/A')}")
                print(f"  Model Version: {result.get('model_version', 'N/A')}")
                print(f"  Mode: {result.get('mode', 'N/A')}")
                
                if result.get('mode') == 'honeypot':
                    print("  HONEYPOT DETECTED - Deception working!")
            else:
                print(f"ERROR: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        time.sleep(1)
    
    # Test 4: Fake Crypto Endpoint
    print("\n4. FAKE CRYPTO ENDPOINT TEST")
    print("-" * 30)
    
    crypto_scenarios = [
        {
            "name": "Quantum-Resistant Request",
            "vector": [15000, 0.1, 10, 1.0],
            "capabilities": {
                "protocols": ["aes256", "chacha20_poly1305", "hybrid_pqc_aes256", "full_pqc"],
                "supports_pqc": True,
                "supports_hybrid": True
            }
        },
        {
            "name": "Standard Encryption",
            "vector": [5000, 0.5, 3, 0.0],
            "capabilities": {
                "protocols": ["aes128", "aes256"],
                "supports_pqc": False,
                "supports_hybrid": False
            }
        }
    ]
    
    for scenario in crypto_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print(f"Vector: {scenario['vector']}")
        print(f"Capabilities: {scenario['capabilities']}")
        
        payload = {
            "token": f"crypto_test_{scenario['name'].replace(' ', '_').lower()}",
            "vector": scenario["vector"],
            "client_capabilities": scenario["capabilities"],
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(
                f"{base_url}/ml/fake-crypto",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: Crypto response received")
                print(f"  Risk: {result.get('risk', 'N/A')}")
                
                if 'crypto_recommendation' in result:
                    rec = result['crypto_recommendation']
                    print(f"  Protocol: {rec.get('recommended_protocol', 'N/A')}")
                    print(f"  Strength: {rec.get('crypto_strength', 'N/A')}")
                    print(f"  PQC Required: {rec.get('pqc_required', 'N/A')}")
                
                if 'honeypot_indicators' in result:
                    indicators = result['honeypot_indicators']
                    print(f"  Decoy Crypto: {indicators.get('decoy_crypto', False)}")
                    print(f"  Fake Negotiation: {indicators.get('fake_negotiation', False)}")
            else:
                print(f"ERROR: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        time.sleep(1)
    
    # Test 5: Fake Admin Endpoint
    print("\n5. FAKE ADMIN ENDPOINT TEST")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/admin/fake-health")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Fake admin response received")
            print(f"  Status: {result.get('status', 'N/A')}")
            
            if 'fake_metrics' in result:
                metrics = result['fake_metrics']
                print(f"  CPU: {metrics.get('cpu', 'N/A')}%")
                print(f"  Memory: {metrics.get('memory', 'N/A')}%")
            
            if 'honeypot_data' in result:
                honeypot_data = result['honeypot_data']
                print(f"  Fake Alerts: {honeypot_data.get('fake_alerts', [])}")
                print(f"  Fake Models: {honeypot_data.get('fake_models', [])}")
                print(f"  Decoy Status: {honeypot_data.get('decoy_status', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 6: Intelligence Report
    print("\n6. INTELLIGENCE REPORT TEST")
    print("-" * 30)
    
    # Generate some test interactions first
    print("Generating test interactions...")
    test_vectors = [
        [30000, 0.01, 20, 1.0],  # Massive attack
        [12000, 0.2, 8, 1.0],    # Medium attack
        [5000, 0.8, 3, 0.0],     # Normal looking
    ]
    
    for i, vector in enumerate(test_vectors):
        try:
            payload = {
                "token": f"intelligence_test_{i+1}",
                "vector": vector,
                "timestamp": time.time()
            }
            
            # Test fake ML endpoint
            requests.post(
                f"{base_url}/ml/fake-score",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Test fake crypto endpoint
            crypto_payload = {
                "token": f"crypto_intelligence_test_{i+1}",
                "vector": vector,
                "client_capabilities": {
                    "protocols": ["aes256", "chacha20_poly1305"],
                    "supports_pqc": True,
                    "supports_hybrid": True
                },
                "timestamp": time.time()
            }
            
            requests.post(
                f"{base_url}/ml/fake-crypto",
                json=crypto_payload,
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            print(f"Warning: Failed to generate test interaction: {e}")
        
        time.sleep(0.5)
    
    # Wait for intelligence processing
    time.sleep(2)
    
    try:
        response = requests.get(
            f"{base_url}/admin/honeypot/intelligence",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Intelligence report received")
            print(f"  Active Honeypots: {result.get('active_honeypots', 'N/A')}")
            print(f"  Total Interactions: {result.get('total_interactions', 'N/A')}")
            print(f"  Attacker Profiles: {result.get('attacker_profiles', 'N/A')}")
            print(f"  High Threat Attackers: {result.get('high_threat_attackers', 'N/A')}")
            print(f"  Intelligence Data Points: {result.get('intelligence_data_points', 'N/A')}")
            print(f"  Monitoring Status: {result.get('monitoring_status', 'N/A')}")
            
            if 'threat_summary' in result:
                summary = result['threat_summary']
                print(f"\n  Threat Summary:")
                print(f"    Total Attackers: {summary.get('total_attackers', 'N/A')}")
                
                if 'threat_distribution' in summary:
                    dist = summary['threat_distribution']
                    print(f"    Threat Distribution:")
                    print(f"      Critical: {dist.get('critical', 0)}")
                    print(f"      High: {dist.get('high', 0)}")
                    print(f"      Medium: {dist.get('medium', 0)}")
                    print(f"      Low: {dist.get('low', 0)}")
                
                if 'recommendations' in summary:
                    print(f"    Security Recommendations:")
                    for rec in summary['recommendations']:
                        print(f"      - {rec}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 7: Real vs Fake Comparison
    print("\n7. REAL VS FAKE ENDPOINT COMPARISON")
    print("-" * 30)
    
    test_vector = [15000, 0.1, 10, 1.0]
    payload = {
        "token": "comparison_test",
        "vector": test_vector,
        "timestamp": time.time()
    }
    
    print(f"Testing with vector: {test_vector}")
    
    # Test real endpoint
    print("\nReal endpoint (/ml/score):")
    try:
        response = requests.post(
            f"{base_url}/ml/score",
            json=payload,
            headers={"Content-Type": "application/json", "x-api-key": api_key}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  SUCCESS: Real endpoint response")
            print(f"  Risk: {result.get('risk', 'N/A')}")
            print(f"  Action: {result.get('action', 'N/A')}")
            print(f"  Mode: {result.get('mode', 'N/A')}")
            print(f"  Model Version: {result.get('model_version', 'N/A')}")
        else:
            print(f"  ERROR: Real endpoint error: {response.status_code}")
    except Exception as e:
        print(f"  ERROR: Real endpoint exception: {e}")
    
    # Test fake endpoint
    print("\nFake endpoint (/ml/fake-score):")
    try:
        response = requests.post(
            f"{base_url}/ml/fake-score",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  SUCCESS: Fake endpoint response")
            print(f"  Risk: {result.get('risk', 'N/A')}")
            print(f"  Action: {result.get('action', 'N/A')}")
            print(f"  Mode: {result.get('mode', 'N/A')}")
            print(f"  Model Version: {result.get('model_version', 'N/A')}")
            
            if 'fake_indicators' in result:
                indicators = result['fake_indicators']
                print(f"  Honeypot Detected: {indicators.get('honeypot_detected', False)}")
                print(f"  Fake Timestamp: {indicators.get('fake_timestamp', 'N/A')}")
                print(f"  Decoy Features: {indicators.get('decoy_features', [])}")
        else:
            print(f"  ERROR: Fake endpoint error: {response.status_code}")
    except Exception as e:
        print(f"  ERROR: Fake endpoint exception: {e}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("HONEYPOT INTELLIGENCE TEST COMPLETE")
    print("=" * 50)
    print("The honeypot intelligence network provides:")
    print("1. DECEPTION: Fake responses confuse attackers")
    print("2. INTELLIGENCE: Gathers data on attack patterns")
    print("3. PROFILING: Creates attacker behavioral profiles")
    print("4. COUNTER-INTELLIGENCE: Uses intelligence to improve defenses")
    print("5. MILITARY-GRADE: Suitable for high-security environments")
    print("=" * 50)

if __name__ == "__main__":
    test_honeypot_system()
