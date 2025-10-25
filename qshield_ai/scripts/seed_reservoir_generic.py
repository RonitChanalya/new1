# scripts/seed_reservoir_generic.py
"""
Generic seeder for ReservoirBuffer.
It tries to detect add/push/persist methods and uses them.
Run: python .\scripts\seed_reservoir_generic.py
"""

import time, random, json, os
from importlib import import_module

def gen_normal():
    return [
        float(random.gauss(800.0, 200.0)),   # padded_size bytes
        float(max(0.01, abs(random.gauss(30.0, 20.0)))), # interval
        float(random.choice([1,1,1,2])),     # dest_count
        0.0                                   # device_change_flag
    ]

def gen_anom():
    return [
        float(random.gauss(12000.0, 2000.0)),
        float(random.uniform(0.01, 0.5)),
        float(random.choice([5,10,20])),
        1.0
    ]

# Try to import ReservoirBuffer
try:
    mod = import_module("reservoir_buffer")
    ReservoirBuffer = getattr(mod, "ReservoirBuffer")
except Exception as e:
    print("[seed] failed to import ReservoirBuffer:", e)
    raise SystemExit(1)

rb = ReservoirBuffer()  # instantiate

print("[seed] ReservoirBuffer instance created:", rb)

# Inspect available methods
methods = {name: getattr(rb, name) for name in dir(rb) if callable(getattr(rb, name))}
print("[seed] detected methods:", sorted([m for m in methods.keys() if not m.startswith("_")]))

# We will try common method names in order:
insert_methods = ["add", "push", "append", "push_observation", "ingest", "observe", "insert"]
persist_methods = ["persist", "save", "flush", "write"]

used_insert = None
for name in insert_methods:
    if name in methods:
        used_insert = name
        break

used_persist = None
for name in persist_methods:
    if name in methods:
        used_persist = name
        break

if used_insert is None:
    print("[seed] No obvious insert method found. Showing methods above. Stopping.")
    raise SystemExit(1)

print(f"[seed] using insert method: {used_insert}; persist method: {used_persist}")

# create and insert samples
N_NORMAL = 300
N_ANOMALY = 30
count = 0
now = time.time()

for i in range(N_NORMAL):
    rec = {"token_hash": f"demo_norm_{i}", "vector": gen_normal(), "ts": now - random.uniform(0,3600)}
    try:
        getattr(rb, used_insert)(rec)
        count += 1
    except Exception as e:
        print("[seed] insert error for normal sample:", e)
        break

for i in range(N_ANOMALY):
    rec = {"token_hash": f"demo_anom_{i}", "vector": gen_anom(), "ts": now - random.uniform(0,600)}
    try:
        getattr(rb, used_insert)(rec)
        count += 1
    except Exception as e:
        print("[seed] insert error for anomaly sample:", e)
        break

print(f"[seed] inserted approx {count} samples via {used_insert}")

# call persist if available
if used_persist:
    try:
        getattr(rb, used_persist)()
        print(f"[seed] called persist method {used_persist}()")
    except Exception as e:
        print("[seed] persist call failed:", e)

# Try to show buffer size if attribute exists
for attr in ("size", "count", "__len__"):
    if hasattr(rb, attr):
        try:
            val = getattr(rb, attr)() if callable(getattr(rb, attr)) else getattr(rb, attr)
            print("[seed] buffer", attr, "=", val)
        except Exception:
            pass

# fallback: try len(rb) if implemented
try:
    print("[seed] len(rb) =>", len(rb))
except Exception:
    pass

print("[seed] done.")
