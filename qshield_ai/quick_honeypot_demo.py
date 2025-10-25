#!/usr/bin/env python3
"""
Quick Honeypot Intelligence Demo
Shows the honeypot system in action with realistic scenarios
"""
import requests
import json
import time

def quick_demo():
    """Quick demonstration of honeypot intelligence capabilities"""
    
    base_url = "http://127.0.0.1:8000"
    api_key = "5ac00dc6a40ea9ddbe0e341bbd3537b1"
    headers = {"x-api-key": api_key}
    
    print("QUICK HONEYPOT INTELLIGENCE DEMO")
    print("=" * 40)
    print("Demonstrating military-grade honeypot intelligence")
    print("=" * 40)
    
    # Scenario 1: Attacker reconnaissance
    print("\nSCENARIO 1: ATTACKER RECONNAISSANCE")
    print("-" * 35)
    print("Attacker probes fake admin endpoint...")
    
    try:
        response = requests.get(f"{base_url}/admin/fake-health")
        if response.status_code == 200:
            result = response.json()
            print("Attacker sees fake system status:")
            print(f"  Status: {result.get('status', 'operational')}")
            if 'fake_metrics' in result:
                metrics = result['fake_metrics']
                print(f"  CPU Usage: {metrics.get('cpu', 45)}%")
                print(f"  Memory Usage: {metrics.get('memory', 67)}%")
            print("  -> Attacker thinks they found real admin panel!")
    except Exception as e:
        print(f"Error: {e}")
    
    # Scenario 2: Attack attempt
    print("\nSCENARIO 2: ATTACK ATTEMPT")
    print("-" * 35)
    print("Attacker tries to exploit ML system...")
    
    attack_vector = [25000, 0.05, 15, 1.0]  # Massive file, rapid, many recipients
    print(f"Attack vector: {attack_vector}")
    
    payload = {
        "token": "suspicious_attacker",
        "vector": attack_vector,
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
            print("Honeypot response:")
            print(f"  Risk Score: {result.get('risk', 15)}")
            print(f"  Action: {result.get('action', 'block')}")
            print(f"  Model Version: {result.get('model_version', 'v1.5_fake')}")
            print("  -> Attacker gets fake response, system gathers intelligence!")
    except Exception as e:
        print(f"Error: {e}")
    
    # Scenario 3: Crypto negotiation attack
    print("\nSCENARIO 3: CRYPTO NEGOTIATION ATTACK")
    print("-" * 35)
    print("Attacker tries to negotiate weak encryption...")
    
    crypto_payload = {
        "token": "crypto_attacker",
        "vector": [18000, 0.1, 12, 1.0],
        "client_capabilities": {
            "protocols": ["aes128"],  # Only weak encryption
            "supports_pqc": False,
            "supports_hybrid": False
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
            print("Honeypot crypto response:")
            print(f"  Risk: {result.get('risk', 25)}")
            if 'crypto_recommendation' in result:
                rec = result['crypto_recommendation']
                print(f"  Protocol: {rec.get('recommended_protocol', 'aes128_fake')}")
                print(f"  Strength: {rec.get('crypto_strength', 'Standard Military')}")
            print("  -> Attacker thinks they got weak encryption, but it's fake!")
    except Exception as e:
        print(f"Error: {e}")
    
    # Scenario 4: Intelligence gathering
    print("\nSCENARIO 4: INTELLIGENCE GATHERING")
    print("-" * 35)
    print("System analyzes attacker behavior...")
    
    try:
        response = requests.get(
            f"{base_url}/admin/honeypot/intelligence",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Intelligence report:")
            print(f"  Active Honeypots: {result.get('active_honeypots', 3)}")
            print(f"  Total Interactions: {result.get('total_interactions', 0)}")
            print(f"  Attacker Profiles: {result.get('attacker_profiles', 0)}")
            print(f"  Monitoring Status: {result.get('monitoring_status', 'active')}")
            print("  -> System has gathered intelligence on attacker behavior!")
        else:
            print(f"Error getting intelligence: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Summary
    print("\n" + "=" * 40)
    print("HONEYPOT INTELLIGENCE DEMO COMPLETE")
    print("=" * 40)
    print("What happened:")
    print("1. Attacker probed fake admin panel (deception)")
    print("2. Attacker tried ML attack (intelligence gathered)")
    print("3. Attacker negotiated crypto (behavior profiled)")
    print("4. System analyzed all interactions (counter-intelligence)")
    print("\nResult: Attacker is confused, system is smarter!")
    print("=" * 40)

if __name__ == "__main__":
    quick_demo()
