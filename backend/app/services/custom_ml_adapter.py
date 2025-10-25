# backend/app/services/custom_ml_adapter.py
"""
Adapter wrapper for the teammate's detector_module.py so the backend can call:
  ml.add_observation(vector)
  ml.score(vector) -> int (0..100)
  ml.force_retrain() -> bool
  ml.health() -> dict

This adapter imports detector_module (the file you pasted) and uses its
functions/variables (buffer, buffer_lock, model, scaler, trained, etc.)
so we don't duplicate training logic.
"""

from typing import List, Dict, Any
import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

try:
    import detector_module  # the ML code provided by your teammate
    DETECTOR_AVAILABLE = True
except Exception as e:
    detector_module = None
    DETECTOR_AVAILABLE = False
    logger.exception("detector_module import failed; custom ML unavailable: %s", e)


class DetectorModuleAdapter:
    def __init__(self):
        self.available = DETECTOR_AVAILABLE
        if self.available:
            # detector_module runs its retrain thread and load_model() on import
            logger.info("DetectorModuleAdapter initialized; detector_module available=%s", self.available)
        else:
            logger.info("DetectorModuleAdapter initialized but detector_module not available")

    def add_observation(self, vector: List[float]) -> None:
        if not self.available:
            return
        try:
            # append into detector_module.buffer under its lock (same semantics as module endpoints)
            with detector_module.buffer_lock:
                detector_module.buffer.append([float(x) for x in vector])
                detector_module.metrics["ml_observations_total"] = detector_module.metrics.get("ml_observations_total", 0) + 1
        except Exception:
            logger.exception("Failed to add_observation to detector buffer; skipping")

    def score(self, vector: List[float]) -> int:
        """
        Return 0..100 risk score (higher = safer) using detector_module's model if present.
        Fallback conservative value if not trained/available.
        """
        if not self.available:
            return 50
        try:
            if not (getattr(detector_module, "trained", False) and getattr(detector_module, "model", None) is not None and getattr(detector_module, "scaler", None) is not None):
                # conservative risk if model not ready
                return 80

            X = np.array([vector], dtype=float)
            Xs = detector_module.scaler.transform(X)
            decision_val = float(detector_module.model.decision_function(Xs)[0])
            # use detector_module's own mapping helper if present
            if hasattr(detector_module, "score_to_risk"):
                risk = int(detector_module.score_to_risk(decision_val))
            else:
                # default mapping: 50 + decision_val*50
                risk = int(max(0, min(100, 50 + decision_val * 50)))
            # increment metric if present
            detector_module.metrics["ml_score_calls_total"] = detector_module.metrics.get("ml_score_calls_total", 0) + 1
            return int(risk)
        except Exception:
            logger.exception("Custom detector scoring failed; falling back to conservative risk=50")
            return 50

    def force_retrain(self) -> bool:
        """
        Trigger a retrain using detector_module's retrain function if available.
        Returns True if retrain performed.
        """
        if not self.available:
            return False
        try:
            if hasattr(detector_module, "retrain_model_force"):
                detector_module.retrain_model_force()
                return True
            # no retrain API present
            return False
        except Exception:
            logger.exception("Detector retrain failed")
            return False

    def health(self) -> Dict[str, Any]:
        if not self.available:
            return {"available": False}
        try:
            return {
                "available": True,
                "trained": bool(getattr(detector_module, "trained", False)),
                "buffer_size": len(getattr(detector_module, "buffer", [])),
                "model_version": getattr(detector_module, "model_version", None),
                "last_retrain_ts": getattr(detector_module, "last_retrain_ts", None),
            }
        except Exception:
            logger.exception("Failed to get detector health")
            return {"available": False}
