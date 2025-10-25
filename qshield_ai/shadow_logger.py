# shadow_logger.py
import json
import time
from pathlib import Path
from config import BASE_DIR, get

LOG_FILE = Path(__file__).resolve().parent / "data" / "shadow.log"
LOG_FILE.parent.mkdir(exist_ok=True, parents=True)

def log_decision(token_hash, vector, score, action, model_version=None, meta=None):
    entry = {
        "ts": int(time.time()),
        "token": token_hash,
        "vector": vector,
        "score": score,
        "action": action,
        "model_version": model_version,
        "meta": meta or {}
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
