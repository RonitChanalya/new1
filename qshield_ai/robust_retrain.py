# robust_retrain.py
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
import joblib, json, time
from pathlib import Path
from reservoir_buffer import ReservoirBuffer
from config import MODEL_DIR, get
import os
from adversarial_robustness import AdversarialRobustness
from threat_monitoring import threat_monitor
BUFFER_PATH = Path(__file__).resolve().parent / "data" / "ml_buffer.jsonl"
if not BUFFER_PATH.exists():
    print(f"[Warning] Buffer not found at {BUFFER_PATH}")


MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

IF_PATH = MODEL_DIR / "if_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
SUP_PATH = MODEL_DIR / "sup_model.joblib"
META_PATH = MODEL_DIR / "model_meta.json"

def load_buffer_samples(limit=1000):
    """Load samples from the reservoir buffer file"""
    if not BUFFER_PATH.exists():
        print(f"[load_buffer_samples] Buffer file not found at {BUFFER_PATH}")
        return np.array([])
    
    data = []
    with open(BUFFER_PATH, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                # Convert to tuple format: (token_hash, vector, ts)
                data.append((entry["token_hash"], entry["vector"], entry["ts"]))
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[load_buffer_samples] Skipping malformed line: {e}")
                continue
    
    # data entries: (token_hash, vector, ts)
    vecs = [d[1] for d in data[:limit]]
    return np.array(vecs)

def generate_synthetic_adversarial(n=100):
    # Make adversarial patterns: large size, small interval, many recipients, device_change=1
    adv = []
    for _ in range(n):
        size = np.random.uniform(5000, 20000)  # very large
        interval = np.random.uniform(0.0, 0.5)
        dest_count = np.random.randint(5, 20)
        device_change = 1.0
        # maybe include small random dims if buffer vectors have more dims
        adv.append([size, interval, dest_count, device_change])
    return np.array(adv)

def trim_extremes(X, lower_q=0.01, upper_q=0.99):
    # clip to percentile range
    lower = np.quantile(X, lower_q, axis=0)
    upper = np.quantile(X, upper_q, axis=0)
    X_trim = np.clip(X, lower, upper)
    return X_trim

def robust_retrain_with_adversarial(save_meta=True):
    """Enhanced retraining with adversarial robustness"""
    print("[robust_retrain] Starting robust retraining with adversarial defense...")
    
    # Load normal data
    X = load_buffer_samples(limit=get("MAX_BUFFER"))
    if X.size == 0:
        print("[robust_retrain] No samples in buffer, aborting.")
        return False
    
    print(f"[robust_retrain] Loaded {len(X)} normal samples")
    
    # Initialize adversarial robustness
    adversarial_robustness = AdversarialRobustness()
    
    # Generate adversarial examples
    print("[robust_retrain] Generating adversarial examples...")
    adversarial_samples = adversarial_robustness.generate_adversarial_examples(X, n_samples=max(200, int(0.3 * len(X))))
    print(f"[robust_retrain] Generated {len(adversarial_samples)} adversarial samples")
    
    # Robust preprocessing
    X_robust = adversarial_robustness.robust_feature_engineering(X)
    adv_robust = adversarial_robustness.robust_feature_engineering(adversarial_samples)
    
    # Combine datasets
    X_combined = np.vstack([X_robust, adv_robust])
    y_combined = np.hstack([np.zeros(len(X_robust)), np.ones(len(adv_robust))])
    
    # Train robust ensemble
    contamination = min(0.1, len(adv_robust) / len(X_combined))
    
    # Enhanced Isolation Forest
    if_model = IsolationForest(
        n_estimators=500,  # More estimators for robustness
        contamination=contamination,
        random_state=42,
        max_samples=0.8,  # Bootstrap sampling
        max_features=0.8  # Feature subsampling
    )
    if_model.fit(X_combined)
    
    # Enhanced Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_split=3,
        min_samples_leaf=1,
        random_state=42,
        class_weight='balanced',
        max_features='sqrt'  # Feature subsampling
    )
    rf_model.fit(X_combined, y_combined)
    
    # Robust scaler
    robust_scaler = RobustScaler()
    robust_scaler.fit(X_combined)
    
    # Save models
    joblib.dump(if_model, IF_PATH)
    joblib.dump(rf_model, SUP_PATH)
    joblib.dump(robust_scaler, SCALER_PATH)
    
    # Enhanced metadata
    meta = {
        "trained_at": time.time(),
        "n_normal_samples": int(len(X)),
        "n_adversarial_samples": int(len(adversarial_samples)),
        "contamination": contamination,
        "robust_training": True,
        "adversarial_defense": True,
        "model_version": "v2.0_robust"
    }
    
    if save_meta:
        with open(META_PATH, "w") as f:
            json.dump(meta, f, indent=2)
    
    # Start monitoring
    threat_monitor.start_monitoring()
    
    print("[robust_retrain] Robust models saved with adversarial defense.")
    print(f"[robust_retrain] Model version: {meta['model_version']}")
    
    return True

if __name__ == "__main__":
    robust_retrain_with_adversarial()
