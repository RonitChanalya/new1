# admin_tools.py
import secrets, joblib, shutil, time
from config import set_kv, get, CONF_FILE, BASE_DIR
from pathlib import Path
import os
from config import CONF_FILE as CONF_PATH

def rotate_api_key():
    new = secrets.token_hex(16)
    set_kv("ML_API_KEY", new)
    print(f"[admin] New ML_API_KEY: {new} (persisted in config)")
    return new

def rotate_feature_hmac():
    new = secrets.token_hex(16)
    set_kv("FEATURE_HMAC_KEY", new)
    print(f"[admin] New FEATURE_HMAC_KEY set.")
    return True

def set_mode(mode: str):
    assert mode in ("live","shadow","disabled")
    set_kv("ML_MODE", mode)
    print(f"[admin] ML_MODE set to {mode}")

def snapshot_model():
    # copy model artifacts to snapshot with timestamp
    MODEL_DIR = Path(__file__).resolve().parent / "models"
    ts = int(time.time())
    dst = MODEL_DIR / f"snapshot_{ts}"
    dst.mkdir(exist_ok=True)
    for f in MODEL_DIR.glob("*joblib"):
        shutil.copy(f, dst / f.name)
    print(f"[admin] model snapshot stored in {dst}")
