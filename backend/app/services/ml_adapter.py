# backend/app/services/ml_adapter.py
"""
Production-ready ML adapter using IsolationForest.

Features:
- IsolationForest training and scoring
- Persistent model file (joblib)
- Thread-safe buffer and retrain loop
- Configurable via environment variables
- Optional Prometheus metrics (if prometheus_client installed)
- Deterministic, reproducible training using random_state
- API:
    ml.add_observation(vector: List[float]) -> None
    ml.score(vector: List[float]) -> int   # 0..100 (lower -> more suspicious)
    ml.set_mode('isolation_forest')        # set mode; default 'isolation_forest' if sklearn present
    ml.force_retrain()                     # admin-triggered retrain
    ml.health() -> dict                    # status info
"""

from typing import List, Optional, Dict, Any
import threading
import time
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Optional imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# Optional prometheus
try:
    from prometheus_client import Counter, Gauge
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False

# Config via env vars with sane defaults
MODEL_PATH = os.environ.get("ML_MODEL_PATH", "/data/ml/isolation_forest.joblib")
MODEL_CHECKPOINT_DIR = os.environ.get("ML_MODEL_DIR", "/data/ml")
RETRAIN_INTERVAL = int(os.environ.get("ML_RETRAIN_INTERVAL_SEC", "30"))  # retrain every 30s for prototype; increase in prod
MIN_TRAIN_SAMPLES = int(os.environ.get("ML_MIN_TRAIN_SAMPLES", "200"))
MAX_BUFFER = int(os.environ.get("ML_MAX_BUFFER", "10000"))
CONTAMINATION = float(os.environ.get("ML_CONTAMINATION", "0.02"))  # expected fraction of outliers
RANDOM_STATE = int(os.environ.get("ML_RANDOM_STATE", "42"))
SCALE_FEATURES = os.environ.get("ML_SCALE_FEATURES", "true").lower() in ("1", "true", "yes")
PERSIST_MODEL = os.environ.get("ML_PERSIST_MODEL", "true").lower() in ("1", "true", "yes")

if PROM_AVAILABLE:
    SCORE_CALLS = Counter("ml_score_calls_total", "Number of times score() called")
    OBSERVATIONS = Counter("ml_observations_total", "Number of observations added")
    LAST_RETRAIN = Gauge("ml_last_retrain_timestamp", "Last retrain timestamp")

class ProductionMLAdapter:
    def __init__(self):
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn or joblib not available. Install scikit-learn and joblib to enable IsolationForest.")
            raise RuntimeError("Missing scikit-learn / joblib")

        # model components
        self._model: Optional[IsolationForest] = None
        self._scaler: Optional[StandardScaler] = None
        self._mode = "isolation_forest"
        self._buffer: List[List[float]] = []
        self._lock = threading.RLock()
        self._max_buffer = MAX_BUFFER
        self._min_samples = MIN_TRAIN_SAMPLES
        self._retrain_interval = RETRAIN_INTERVAL
        self._contamination = CONTAMINATION
        self._random_state = RANDOM_STATE
        self._trained = False
        self._shutdown = False

        # attempt to load model if exists
        if PERSIST_MODEL and os.path.exists(MODEL_PATH):
            try:
                state = joblib.load(MODEL_PATH)
                # state expected: dict with keys 'model' and 'scaler'
                self._model = state.get("model")
                self._scaler = state.get("scaler")
                self._trained = True
                logger.info("Loaded persisted ML model from %s", MODEL_PATH)
            except Exception:
                logger.exception("Failed to load persisted ML model; will train fresh.")

        # start retrain background thread
        self._retrain_thread = threading.Thread(target=self._periodic_retrain_loop, daemon=True)
        self._retrain_thread.start()
        logger.info("ProductionMLAdapter initialized; retrain thread started.")

    def add_observation(self, vector: List[float]) -> None:
        try:
            vec = [float(x) for x in vector]
        except Exception:
            logger.exception("Invalid vector in add_observation; skipping")
            return
        with self._lock:
            self._buffer.append(vec)
            if len(self._buffer) > self._max_buffer:
                # drop oldest
                self._buffer.pop(0)
        if PROM_AVAILABLE:
            OBSERVATIONS.inc()

    def _prepare_training_data(self) -> Optional[np.ndarray]:
        with self._lock:
            if len(self._buffer) < self._min_samples:
                return None
            X = np.array(self._buffer, dtype=float)
        # optional scaling
        if SCALE_FEATURES:
            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            return (Xs, scaler)
        return (X, None)

    def _train_model(self, X: np.ndarray, scaler: Optional[StandardScaler]) -> None:
        # instantiate IsolationForest with stable random state
        model = IsolationForest(n_estimators=100, contamination=self._contamination, random_state=self._random_state, n_jobs=-1)
        model.fit(X)
        with self._lock:
            self._model = model
            self._scaler = scaler
            self._trained = True
        logger.info("IsolationForest trained on %d samples; contamination=%s", len(X), self._contamination)
        if PERSIST_MODEL:
            self._persist_model()

    def _persist_model(self) -> None:
        try:
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            state = {"model": self._model, "scaler": self._scaler}
            joblib.dump(state, MODEL_PATH)
            logger.info("Persisted ML model to %s", MODEL_PATH)
        except Exception:
            logger.exception("Failed to persist ML model")

    def force_retrain(self) -> bool:
        """Admin-triggered retrain. Returns True if retrained."""
        prepared = self._prepare_training_data()
        if not prepared:
            logger.warning("Not enough data to retrain (have %d, need %d)", len(self._buffer), self._min_samples)
            return False
        X, scaler = prepared
        try:
            self._train_model(X, scaler)
            if PROM_AVAILABLE:
                LAST_RETRAIN.set(time.time())
            return True
        except Exception:
            logger.exception("force_retrain failed")
            return False

    def score(self, vector: List[float]) -> int:
        """Return risk score 0..100 where lower = more suspicious."""
        if PROM_AVAILABLE:
            SCORE_CALLS.inc()
        try:
            vec = np.array([float(x) for x in vector]).reshape(1, -1)
        except Exception:
            logger.exception("Invalid vector passed to score")
            return 0

        with self._lock:
            if not self._trained or self._model is None:
                # fallback heuristic if not trained
                return self._heuristic_score(vector)

            # scale if scaler exists
            if self._scaler is not None:
                try:
                    vec_scaled = self._scaler.transform(vec)
                except Exception:
                    # if transform fails, fall back to raw
                    vec_scaled = vec
            else:
                vec_scaled = vec

            # decision_function: higher => more normal; lower => anomalous
            try:
                df = float(self._model.decision_function(vec_scaled)[0])
                # scale df to 0..100:
                # choose mapping: df_mean around 0, typical range [-1.0, 1.0]; tune as needed
                scaled = int(max(0, min(100, 50 + df * 50)))
                return scaled
            except Exception:
                logger.exception("Model scoring failed; falling back to heuristic")
                return self._heuristic_score(vector)

    def _heuristic_score(self, vector: List[float]) -> int:
        # safe fallback: conservative scoring moving from earlier hack heuristic
        try:
            padded_size = float(vector[0]) if len(vector) > 0 else 0.0
            interval = float(vector[1]) if len(vector) > 1 else 0.0
            dest_count = float(vector[2]) if len(vector) > 2 else 1.0
            device_change = float(vector[3]) if len(vector) > 3 else 0.0
        except Exception:
            padded_size, interval, dest_count, device_change = 0.0, 0.0, 1.0, 0.0

        score = 70
        if padded_size > 50 * 1024:
            score -= 35
        elif padded_size > 10 * 1024:
            score -= 20
        elif padded_size > 2 * 1024:
            score -= 10

        if interval < 1.0:
            score -= 30
        elif interval < 5.0:
            score -= 10

        if dest_count >= 10:
            score -= 30
        elif dest_count >= 3:
            score -= 12

        if device_change:
            score -= 30

        return int(max(0, min(100, score)))

    def _periodic_retrain_loop(self):
        while not self._shutdown:
            time.sleep(self._retrain_interval)
            try:
                prepared = self._prepare_training_data()
                if not prepared:
                    logger.debug("Not enough data to retrain yet.")
                    continue
                X, scaler = prepared
                self._train_model(X, scaler)
                if PROM_AVAILABLE:
                    LAST_RETRAIN.set(time.time())
            except Exception:
                logger.exception("Periodic retrain failed; will retry later")

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "trained": self._trained,
                "buffer_size": len(self._buffer),
                "model_path": MODEL_PATH if PERSIST_MODEL else None,
                "min_samples": self._min_samples,
                "contamination": self._contamination,
            }

    def shutdown(self) -> None:
        self._shutdown = True
        # join thread if desired (not strictly necessary for daemon threads)

# Module-level singleton
ml = None
try:
    from app.services.custom_ml_adapter import DetectorModuleAdapter
    ml = DetectorModuleAdapter()
    if getattr(ml, "available", False):
        logger.info("Using DetectorModuleAdapter as ML adapter.")
    else:
        raise RuntimeError("custom detector not available")
except Exception:
    logger.info("DetectorModuleAdapter unavailable; checking for ProductionMLAdapter fallback.")
    if SKLEARN_AVAILABLE:
        try:
            ml = ProductionMLAdapter()
            logger.info("Using ProductionMLAdapter as ML adapter.")
        except Exception:
            logger.exception("Failed to initialize ProductionMLAdapter; no ML adapter available.")
            ml = None
    else:
        logger.info("scikit-learn not available; skipping ProductionMLAdapter fallback. ml set to None.")
        ml = None
        