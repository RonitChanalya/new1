#!/usr/bin/env python3
"""
Simple test for Honeypot Intelligence Network
"""
import requests
import json
import time

def test_honeypot_system():
    """Test the honeypot intelligence system"""
    base_url = "http://127.0.0.1:8000"
    
    print("HONEYPOT INTELLIGENCE NETWORK TEST")
    print("=" * 50)
    
    # Test 1: Fake ML Endpoint
    print("\n1. Testing Fake ML Endpoint")
    print("-" * 30)
    
    payload = {
        "token": "test_attacker",
        "vector": [15000, 0.1, 10, 1.0],
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
            print("SUCCESS: Fake ML Response")
            print(f"Risk Score: {result.get('risk', 'N/A')}")
            print(f"Action: {result.get('action', 'N/A')}")
            print(f"Model Version: {result.get('model_version', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Fake Crypto Endpoint
    print("\n2. Testing Fake Crypto Endpoint")
    print("-" * 30)
    
    crypto_payload = {
        "token": "crypto_attacker",
        "vector": [12000, 0.2, 8, 1.0],
        "client_capabilities": {
            "protocols": ["aes256", "chacha20_poly1305"],
            "supports_pqc": True,
            "supports_hybrid": True
        },
        "timestamp": time.time()
    }
    
    try:
        response = requests.post(
            f"{base_url}/ml/fake-crypto",
            json=crypto_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Fake Crypto Response")
            print(f"Risk: {result.get('risk', 'N/A')}")
            if 'crypto_recommendation' in result:
                rec = result['crypto_recommendation']
                print(f"Protocol: {rec.get('recommended_protocol', 'N/A')}")
                print(f"Strength: {rec.get('crypto_strength', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Fake Admin Endpoint
    print("\n3. Testing Fake Admin Endpoint")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/admin/fake-health")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Fake Admin Response")
            print(f"Status: {result.get('status', 'N/A')}")
            if 'fake_metrics' in result:
                metrics = result['fake_metrics']
                print(f"CPU: {metrics.get('cpu', 'N/A')}%")
                print(f"Memory: {metrics.get('memory', 'N/A')}%")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 4: Intelligence Report
    print("\n4. Testing Intelligence Report")
    print("-" * 30)
    
    headers = {"x-api-key": "5ac00dc6a40ea9ddbe0e341bbd3537b1"}
    
    try:
        response = requests.get(
            f"{base_url}/admin/honeypot/intelligence",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Intelligence Report")
            print(f"Active Honeypots: {result.get('active_honeypots', 'N/A')}")
            print(f"Total Interactions: {result.get('total_interactions', 'N/A')}")
            print(f"Attacker Profiles: {result.get('attacker_profiles', 'N/A')}")
            print(f"High Threat Attackers: {result.get('high_threat_attackers', 'N/A')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("HONEYPOT TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_honeypot_system()
