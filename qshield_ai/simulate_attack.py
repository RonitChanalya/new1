# simulate_attack.py
import requests, time, json
from reservoir_buffer import ReservoirBuffer
from secret_transform import transform_observation
from config import get
import random

# If your detector service exposes /ml/observe, set this URL or use local buffer
ML_OBSERVE_URL = "http://127.0.0.1:8000/ml/observe"  # if detector_module has this endpoint

def push_to_local_buffer(token, vector):
    from reservoir_buffer import ReservoirBuffer
    rb = ReservoirBuffer()
    tok_hash, proj = transform_observation(token, vector)
    rb.add(tok_hash, proj, timestamp=time.time())

def simulate_normal(n=100):
    for i in range(n):
        size = random.uniform(200, 1500)
        interval = random.uniform(30, 3600) # seconds
        dest_count = random.randint(1, 3)
        device_change = 0.0
        vec = [size, interval, dest_count, device_change]
        push_to_local_buffer(f"user_{random.randint(1,20)}", vec)

def simulate_attack(n=20):
    for i in range(n):
        size = random.uniform(10000, 20000)
        interval = random.uniform(0.0, 0.5)
        dest_count = random.randint(5, 20)
        device_change = 1.0
        vec = [size, interval, dest_count, device_change]
        push_to_local_buffer("honeypot", vec)

if __name__ == "__main__":
    print("Simulating normal traffic...")
    simulate_normal(200)
    print("Simulating adversarial traffic...")
    simulate_attack(60)
    print("Done. Run robust_retrain.py to rebuild models.")
