# config.py
import os
import json
from pathlib import Path
from secrets import token_hex

# default config values (can be overridden by env vars)
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# persisted simple config file
CONF_FILE = BASE_DIR / "ml_runtime_config.json"

DEFAULT = {
    "ML_MODE": "live",  # live | shadow | disabled
    "ML_API_KEY": os.environ.get("ML_API_KEY", token_hex(16)),
    "FEATURE_HMAC_KEY": os.environ.get("FEATURE_HMAC_KEY", token_hex(16)),
    "MIN_TRAIN_SAMPLES": int(os.environ.get("ML_MIN_TRAIN_SAMPLES", 50)),
    "MAX_BUFFER": int(os.environ.get("ML_MAX_BUFFER", 2000)),
    "CONTAMINATION": float(os.environ.get("ML_CONTAMINATION", 0.03)),
    "CONSENSUS_N": 3,  # number of detectors in ensemble
    "CONSENSUS_THRESHOLD": 2,  # require 2/3 detectors to flag
    "THRESH_ALLOW": 60,  # risk threshold for allowing messages
    "THRESH_REAUTH": 40,  # risk threshold for requiring re-authentication
    "FALLBACK_RISK": 50,  # default risk when model not trained
    "OBSERVE_ON_SCORE": False  # whether to log observations during scoring
}

def _init_conf():
    if not CONF_FILE.exists():
        with open(CONF_FILE, "w") as f:
            json.dump(DEFAULT, f, indent=2)
    with open(CONF_FILE) as f:
        return json.load(f)

_conf = _init_conf()

def get(k):
    return _conf.get(k, DEFAULT.get(k))

def set_kv(k, v):
    _conf[k] = v
    with open(CONF_FILE, "w") as f:
        json.dump(_conf, f, indent=2)
