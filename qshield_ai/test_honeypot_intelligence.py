#!/usr/bin/env python3
"""
Test script for Honeypot Intelligence Network
Demonstrates deployment, interaction, and intelligence gathering
"""
import requests
import json
import time
import random
from typing import Dict, List

class HoneypotTester:
    """Test the honeypot intelligence system"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str = "5ac00dc6a40ea9ddbe0e341bbd3537b1"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}
    
    def test_fake_ml_endpoint(self):
        """Test fake ML scoring endpoint"""
        print("Testing Fake ML Endpoint (Honeypot)")
        print("=" * 50)
        
        # Simulate different attack patterns
        attack_vectors = [
            [15000, 0.1, 10, 1.0],  # Obvious attack
            [8000, 0.5, 5, 1.0],    # Medium attack
            [2000, 1.0, 2, 0.0],    # Normal looking
            [25000, 0.05, 15, 1.0], # Extreme attack
        ]
        
        for i, vector in enumerate(attack_vectors):
            print(f"\n🎯 Attack Vector {i+1}: {vector}")
            
            payload = {
                "token": f"attacker_{i+1}",
                "vector": vector,
                "timestamp": time.time()
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/ml/fake-score",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"SUCCESS: Honeypot Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"ERROR: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"ERROR: Request failed: {e}")
            
            time.sleep(1)  # Pause between requests
    
    def test_fake_crypto_endpoint(self):
        """Test fake crypto negotiation endpoint"""
        print("\n🔐 Testing Fake Crypto Endpoint (Honeypot)")
        print("=" * 50)
        
        # Simulate different crypto capabilities
        crypto_scenarios = [
            {
                "vector": [12000, 0.2, 8, 1.0],
                "client_capabilities": {
                    "protocols": ["aes128", "aes256"],
                    "supports_pqc": False,
                    "supports_hybrid": False
                }
            },
            {
                "vector": [18000, 0.1, 12, 1.0],
                "client_capabilities": {
                    "protocols": ["aes256", "chacha20_poly1305", "hybrid_pqc_aes256"],
                    "supports_pqc": True,
                    "supports_hybrid": True
                }
            }
        ]
        
        for i, scenario in enumerate(crypto_scenarios):
            print(f"\n🔑 Crypto Scenario {i+1}:")
            print(f"   Vector: {scenario['vector']}")
            print(f"   Capabilities: {scenario['client_capabilities']}")
            
            payload = {
                "token": f"crypto_attacker_{i+1}",
                "vector": scenario["vector"],
                "client_capabilities": scenario["client_capabilities"],
                "timestamp": time.time()
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/ml/fake-crypto",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Honeypot Crypto Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            time.sleep(1)
    
    def test_fake_admin_endpoint(self):
        """Test fake admin endpoint"""
        print("\n👤 Testing Fake Admin Endpoint (Honeypot)")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/admin/fake-health")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Fake Admin Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    def test_honeypot_deployment(self):
        """Test honeypot deployment"""
        print("\n🚀 Testing Honeypot Deployment")
        print("=" * 50)
        
        honeypot_types = ["fake_ml_endpoint", "fake_crypto_service", "fake_admin_panel"]
        
        for honeypot_type in honeypot_types:
            try:
                response = requests.post(
                    f"{self.base_url}/admin/honeypot/deploy",
                    params={"honeypot_type": honeypot_type},
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Deployed {honeypot_type}: {result}")
                else:
                    print(f"❌ Failed to deploy {honeypot_type}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Deployment failed for {honeypot_type}: {e}")
    
    def test_intelligence_report(self):
        """Test intelligence report"""
        print("\n📊 Testing Intelligence Report")
        print("=" * 50)
        
        try:
            response = requests.get(
                f"{self.base_url}/admin/honeypot/intelligence",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Intelligence Report: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    def simulate_attacker_behavior(self):
        """Simulate realistic attacker behavior"""
        print("\n🎭 Simulating Attacker Behavior")
        print("=" * 50)
        
        # Simulate reconnaissance phase
        print("🔍 Phase 1: Reconnaissance")
        self._simulate_reconnaissance()
        
        time.sleep(2)
        
        # Simulate exploitation phase
        print("\n⚔️ Phase 2: Exploitation Attempts")
        self._simulate_exploitation()
        
        time.sleep(2)
        
        # Simulate evasion attempts
        print("\n🕵️ Phase 3: Evasion Attempts")
        self._simulate_evasion()
    
    def _simulate_reconnaissance(self):
        """Simulate reconnaissance behavior"""
        # Test fake admin endpoint
        self.test_fake_admin_endpoint()
        
        # Test fake health endpoints
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"✅ Health check: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    def _simulate_exploitation(self):
        """Simulate exploitation attempts"""
        # Try various attack vectors
        attack_vectors = [
            [30000, 0.01, 20, 1.0],  # Massive data exfiltration
            [5000, 0.1, 8, 1.0],     # Medium attack
            [15000, 0.05, 12, 1.0],  # Large file attack
        ]
        
        for i, vector in enumerate(attack_vectors):
            print(f"🎯 Exploitation attempt {i+1}: {vector}")
            
            payload = {
                "token": f"exploit_attacker_{i+1}",
                "vector": vector,
                "timestamp": time.time()
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/ml/fake-score",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                print(f"   Response: {response.status_code}")
            except Exception as e:
                print(f"   Failed: {e}")
            
            time.sleep(0.5)
    
    def _simulate_evasion(self):
        """Simulate evasion attempts"""
        # Try to evade detection with subtle modifications
        evasion_vectors = [
            [12000, 0.8, 6, 1.0],    # Slightly modified
            [8000, 1.2, 4, 0.0],     # More normal looking
            [10000, 0.6, 5, 1.0],    # Medium modification
        ]
        
        for i, vector in enumerate(evasion_vectors):
            print(f"🕵️ Evasion attempt {i+1}: {vector}")
            
            payload = {
                "token": f"evasion_attacker_{i+1}",
                "vector": vector,
                "timestamp": time.time()
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/ml/fake-score",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                print(f"   Response: {response.status_code}")
            except Exception as e:
                print(f"   Failed: {e}")
            
            time.sleep(0.5)
    
    def run_comprehensive_test(self):
        """Run comprehensive honeypot test"""
        print("HONEYPOT INTELLIGENCE NETWORK TEST")
        print("=" * 60)
        print("Testing military-grade honeypot intelligence system")
        print("=" * 60)
        
        # Test basic functionality
        self.test_fake_ml_endpoint()
        self.test_fake_crypto_endpoint()
        self.test_fake_admin_endpoint()
        
        # Test deployment
        self.test_honeypot_deployment()
        
        # Simulate realistic attacker behavior
        self.simulate_attacker_behavior()
        
        # Get intelligence report
        print("\n" + "=" * 60)
        print("📊 FINAL INTELLIGENCE REPORT")
        print("=" * 60)
        self.test_intelligence_report()
        
        print("\n🎯 Honeypot Intelligence Test Complete!")
        print("The system has gathered intelligence on attacker behavior patterns.")

if __name__ == "__main__":
    tester = HoneypotTester()
    tester.run_comprehensive_test()
