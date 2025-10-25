# scripts/warmup_ml.py
# Generate synthetic normal + anomalous vectors into data/ml_buffer.jsonl
import os, json, random, time

OUT_DIR = "data"
OUT_FILE = os.path.join(OUT_DIR, "ml_buffer.jsonl")
os.makedirs(OUT_DIR, exist_ok=True)

def gen_normal():
    # padded_size (bytes), interval (s), dest_count, device_change_flag
    return [
        float(random.gauss(800.0, 200.0)),  # size around 800 bytes
        max(0.05, abs(random.gauss(30.0, 20.0))),  # seconds since last message
        float(random.choice([1,1,1,2])),  # typical small number of recipients
        0.0
    ]

def gen_anomaly():
    return [
        float(random.gauss(12000.0, 2000.0)),  # large payloads
        float(random.uniform(0.01, 0.5)),      # extremely small interval (burst)
        float(random.choice([5,10,20])),       # many recipients
        1.0
    ]

N_NORMAL = 400
N_ANOMALY = 40

with open(OUT_FILE, "w", encoding="utf-8") as f:
    now = time.time()
    for i in range(N_NORMAL):
        rec = {
            "token_hash": f"demo_{random.randrange(1_000_000)}",
            "vector": gen_normal(),
            "ts": now - random.uniform(0, 3600)
        }
        f.write(json.dumps(rec) + "\n")
    for i in range(N_ANOMALY):
        rec = {
            "token_hash": f"demo_anom_{random.randrange(1_000_000)}",
            "vector": gen_anomaly(),
            "ts": now - random.uniform(0, 600)
        }
        f.write(json.dumps(rec) + "\n")

print(f"[warmup_ml] wrote {N_NORMAL + N_ANOMALY} samples -> {OUT_FILE}")
