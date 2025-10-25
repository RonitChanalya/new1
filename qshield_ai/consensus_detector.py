# consensus_detector.py
import joblib
import numpy as np
import os
from pathlib import Path
from config import MODEL_DIR, get

MODEL_DIR = Path(__file__).resolve().parent / "models"

# model name patterns
IF_NAME = MODEL_DIR / "if_model.joblib"
SCALER_NAME = MODEL_DIR / "scaler.joblib"
SUP_NAME = MODEL_DIR / "sup_model.joblib"  # supervised anomaly detector (optional)

def load_models():
    models = {}
    if IF_NAME.exists():
        models['if'] = joblib.load(IF_NAME)
    if SCALER_NAME.exists():
        models['scaler'] = joblib.load(SCALER_NAME)
    if SUP_NAME.exists():
        models['sup'] = joblib.load(SUP_NAME)
    return models

def decision_to_risk(decision_value):
    # decision_value is decision_function output: higher = normal (for IsolationForest)
    # Map to 0..100 where higher = safe
    # scale by heuristic
    r = int(max(0, min(100, 50 + (decision_value * 20))))
    return r

class ConsensusDetector:
    def __init__(self):
        self.models = load_models()
        self.consensus_n = int(get("CONSENSUS_N"))
        self.consensus_threshold = int(get("CONSENSUS_THRESHOLD"))

    def score(self, vector):
        """
        vector: already transformed numeric list
        returns: dict { 'risk': int(0..100), 'flags': { 'if':bool, 'sup':bool }, 'raw': {...}}
        """
        scaler = self.models.get('scaler')
        X = np.array(vector).reshape(1, -1)
        if scaler is not None:
            Xs = scaler.transform(X)
        else:
            Xs = X
        flags = {}
        votes = 0
        risks = []
        # IsolationForest
        if 'if' in self.models:
            if_m = self.models['if']
            dv = if_m.decision_function(Xs)[0]  # higher=normal
            risk = decision_to_risk(dv)
            risks.append(risk)
            flagged = (risk < 40)  # below threshold -> anomaly
            flags['if'] = flagged
            votes += 1 if flagged else 0
        # supervised (if present) - assume outputs probability of anomaly
        if 'sup' in self.models:
            sup_m = self.models['sup']
            p = sup_m.predict_proba(Xs)[0, 1] if hasattr(sup_m, "predict_proba") else sup_m.predict(Xs)[0]
            # convert: p close to 1 = anomaly
            flagged = (p > 0.5)
            flags['sup'] = flagged
            # produce risk complement
            risks.append(int(max(0, min(100, 100 - int(p*100)))))
            votes += 1 if flagged else 0

        # combine risk as average
        if risks:
            combined_risk = int(sum(risks)/len(risks))
        else:
            combined_risk = 50  # default neutral

        action = "allow"
        if votes >= self.consensus_threshold:
            action = "block"
        elif combined_risk < 40:
            action = "require_reauth"

        return {
            "risk": combined_risk,
            "action": action,
            "flags": flags,
            "votes": votes
        }

    def is_trained(self):
        """Check if the detector has trained models"""
        return len(self.models) > 0 and ('if' in self.models or 'sup' in self.models)

    def decision_function(self, vector):
        """Get decision function value for a vector (for compatibility with detector_module)"""
        result = self.score(vector)
        # Convert risk back to decision function value (higher = more normal)
        risk = result["risk"]
        # Map risk (0-100) back to decision function value
        decision_value = (risk - 50) / 25.0  # inverse of the mapping in detector_module
        return decision_value

    def model_version(self):
        """Get model version for logging"""
        if 'if' in self.models:
            return "v1.0"
        return "untrained"

    def metadata(self):
        """Get model metadata for admin interface"""
        meta = {
            "models_loaded": list(self.models.keys()),
            "consensus_n": self.consensus_n,
            "consensus_threshold": self.consensus_threshold,
            "version": self.model_version()
        }
        return meta

# convenience factory
_detector = None
def get_detector():
    global _detector
    if _detector is None:
        _detector = ConsensusDetector()
    return _detector
