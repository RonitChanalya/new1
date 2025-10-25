# detector_module.py
"""
Minimal FastAPI "detector" microservice that plugs your demo helpers together.
Exposes:
 - POST /ml/observe   -> append anonymized vector to reservoir buffer
 - POST /ml/score     -> synchronous scoring (protected by X-API-KEY)
 - GET  /admin/ml/health -> model health
 - POST /admin/ml/retrain -> admin-trigger retrain (protected)
"""
import os
import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

# import demo helpers (these must be in same folder / installed package)
# If your file names differ, adapt these imports.
import config
import reservoir_buffer
import consensus_detector
import robust_retrain
import shadow_logger
import admin_tools
import secret_transform
import adaptive_crypto
import adversarial_robustness
import threat_monitoring
import honeypot_intelligence
import enhanced_ensemble_detector

# Create global reservoir buffer instance
reservoir_buffer = reservoir_buffer.ReservoirBuffer()

# Initialize honeypot intelligence system
honeypot_intelligence.honeypot_intelligence.start_intelligence_monitoring()

# basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("detector")

app = FastAPI(title="Threat Detector (demo)", version="0.1")

# -------------------------------------------------------
# Pydantic request schemas
# -------------------------------------------------------
class ObservePayload(BaseModel):
    token: str
    vector: list
    timestamp: float | None = None

class ScorePayload(BaseModel):
    token: str
    vector: list
    timestamp: float | None = None

class CryptoNegotiationPayload(BaseModel):
    token: str
    vector: list
    client_capabilities: dict
    timestamp: float | None = None

# -------------------------------------------------------
# helpers
# -------------------------------------------------------
def check_api_key(x_api_key: str | None):
    if x_api_key is None or x_api_key != config.get("ML_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

def map_decision_to_risk(decision_value: float) -> int:
    """
    Map IsolationForest.decision_function value -> risk 0..100
    decision_function: higher -> more normal
    We map so that normal -> higher risk score (closer to 100), anomalous -> lower score.
    A simple linear mapping with clamping.
    """
    # scale factor tuned for prototype; adjust after calibration
    risk = int(max(0, min(100, 50 + decision_value * 25)))
    return risk

def policy_from_risk(risk: int) -> str:
    if risk >= config.get("THRESH_ALLOW"):
        return "allow"
    if risk >= config.get("THRESH_REAUTH"):
        return "require_reauth"
    return "block"

# -------------------------------------------------------
# Startup: log model availability
# -------------------------------------------------------
@app.on_event("startup")
def startup_event():
    loaded = consensus_detector.get_detector().is_trained()
    logger.info(f"[detector] ML adapter started. Model loaded: {loaded}")

# -------------------------------------------------------
# Endpoints
# -------------------------------------------------------
@app.post("/ml/observe")
async def ml_observe(payload: ObservePayload, request: Request):
    """
    Ingest an anonymized feature vector into the reservoir buffer.
    This endpoint is intended to be called by backend trusted services.
    """
    try:
        # transform token into hashed/pseudonymized id before storing
        token_hash = secret_transform.hash_token(payload.token)
        vec = [float(x) for x in payload.vector]
        # append (token_hash kept minimal; vector stored) – buffer responsible for retention policy
        reservoir_buffer.add(token_hash, vec, payload.timestamp or time.time())
        return {"status": "ingested", "buffer_size": reservoir_buffer.size()}
    except Exception as e:
        logger.exception("ml_observe failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/score")
async def ml_score(payload: ScorePayload, x_api_key: str | None = Header(None)):
    """
    Synchronous scoring endpoint. Protected by X-API-KEY header.
    Returns risk (0..100) and policy action.
    """
    check_api_key(x_api_key)
    try:
        token_hash = secret_transform.hash_token(payload.token)
        vec = [float(x) for x in payload.vector]

        # Optional: write to observe buffer for continuous learning (configurable)
        if config.get("OBSERVE_ON_SCORE"):
            reservoir_buffer.add(token_hash, vec, payload.timestamp or time.time())

        # get model and score
        detector = consensus_detector.get_detector()
        if not detector.is_trained():
            # fallback heuristic if model not trained
            logger.warning("[detector] model not trained; using heuristic fallback")
            # fallback returns neutral risk
            risk = config.get("FALLBACK_RISK")
            action = policy_from_risk(risk)
            shadow_logger.log_decision(token_hash, vec, risk, action, model_version=None)
            return {"token_hash": token_hash, "mode": "fallback", "risk": risk, "action": action}
        decision_value = detector.decision_function(vec)
        risk = map_decision_to_risk(decision_value)
        action = policy_from_risk(risk)

        # log decision in shadow log (privacy-preserving)
        shadow_logger.log_decision(token_hash, vec, risk, action, model_version=detector.model_version())

        return {"token_hash": token_hash, "mode": "live", "risk": risk, "action": action, "model_version": detector.model_version()}
    except Exception as e:
        logger.exception("ml_score failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/crypto-negotiate")
async def ml_crypto_negotiate(payload: CryptoNegotiationPayload, x_api_key: str | None = Header(None)):
    """
    AI-driven crypto protocol negotiation endpoint.
    Analyzes threat level and recommends appropriate encryption protocol.
    """
    check_api_key(x_api_key)
    try:
        token_hash = secret_transform.hash_token(payload.token)
        vec = [float(x) for x in payload.vector]

        # Get threat assessment
        detector = consensus_detector.get_detector()
        if not detector.is_trained():
            # Fallback for untrained model
            risk = config.get("FALLBACK_RISK")
        else:
            decision_value = detector.decision_function(vec)
            risk = map_decision_to_risk(decision_value)

        # Get AI-driven crypto recommendation
        crypto_recommendation = adaptive_crypto.get_adaptive_crypto_recommendation(
            risk, payload.client_capabilities
        )

        # Log the crypto decision
        shadow_logger.log_decision(
            token_hash, vec, risk, "crypto_negotiation", 
            model_version=detector.model_version() if detector.is_trained() else None,
            meta={"crypto_recommendation": crypto_recommendation}
        )

        return {
            "token_hash": token_hash,
            "risk": risk,
            "crypto_recommendation": crypto_recommendation,
            "model_version": detector.model_version() if detector.is_trained() else "untrained"
        }
    except Exception as e:
        logger.exception("ml_crypto_negotiate failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/enhanced-score")
async def ml_enhanced_score(payload: ScorePayload, x_api_key: str | None = Header(None)):
    """
    Enhanced ensemble scoring with fair feature weighting and multi-model consensus
    """
    check_api_key(x_api_key)
    start_time = time.time()
    
    try:
        token_hash = secret_transform.hash_token(payload.token)
        vec = np.array([float(x) for x in payload.vector]).reshape(1, -1)
        
        # Use enhanced ensemble detector
        enhanced_result = enhanced_ensemble_detector.enhanced_detector.predict(vec)
        
        risk = enhanced_result['risk_score']
        consensus_score = enhanced_result['consensus_score']
        confidence = enhanced_result['confidence']
        consensus_reached = enhanced_result['consensus_reached']
        model_agreement = enhanced_result['model_agreement']
        
        # Determine action based on risk and consensus
        if consensus_reached and confidence > 0.7:
            # High confidence consensus - use ensemble decision
            action = policy_from_risk(risk)
        else:
            # Low confidence or no consensus - be more conservative
            if risk > 70:
                action = "block"  # High risk, block
            elif risk > 50:
                action = "require_reauth"  # Medium risk, reauth
            else:
                action = "allow"  # Low risk, allow
        
        response_time = time.time() - start_time
        
        # Enhanced response with ensemble details
        response = {
            "token_hash": token_hash,
            "mode": "enhanced_ensemble",
            "risk": risk,
            "action": action,
            "consensus_score": round(consensus_score, 3),
            "confidence": round(confidence, 3),
            "consensus_reached": consensus_reached,
            "model_agreement": round(model_agreement, 3),
            "response_time_ms": round(response_time * 1000, 2),
            "ensemble_details": {
                "model_count": len(enhanced_result.get('individual_predictions', {})),
                "model_weights": enhanced_result.get('model_weights', {}),
                "fair_feature_weighting": True
            }
        }
        
        # Log decision with enhanced details
        shadow_logger.log_decision(
            token_hash, vec[0].tolist(), risk, action, 
            model_version="enhanced_ensemble_v1.0",
            meta={
                "consensus_score": consensus_score,
                "confidence": confidence,
                "model_agreement": model_agreement
            }
        )
        
        return response
        
    except Exception as e:
        logger.exception("ml_enhanced_score failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/threat-assessment")
async def ml_threat_assessment(payload: ScorePayload, x_api_key: str | None = Header(None)):
    """
    Enhanced threat assessment with adversarial robustness and monitoring
    """
    check_api_key(x_api_key)
    start_time = time.time()
    
    try:
        token_hash = secret_transform.hash_token(payload.token)
        vec = [float(x) for x in payload.vector]
        
        # Get robust threat assessment
        detector = consensus_detector.get_detector()
        if not detector.is_trained():
            risk = config.get("FALLBACK_RISK")
            uncertainty_score = 0.5
            drift_detected = False
        else:
            # Use robust detection if available
            if hasattr(adversarial_robustness, 'robust_detector') and adversarial_robustness.robust_detector.models:
                robust_result = adversarial_robustness.robust_detector.detect_threat_robust(np.array(vec))
                risk = robust_result['risk_score']
                uncertainty_score = robust_result['uncertainty_score']
                drift_detected = robust_result['drift_detected']
            else:
                # Fallback to standard detection
                decision_value = detector.decision_function(vec)
                risk = map_decision_to_risk(decision_value)
                uncertainty_score = 0.1  # Default low uncertainty
                drift_detected = False
        
        action = policy_from_risk(risk)
        response_time = time.time() - start_time
        
        # Log for monitoring
        prediction_data = {
            'risk_score': risk,
            'uncertainty_score': uncertainty_score,
            'response_time': response_time,
            'features': vec,
            'model_version': detector.model_version() if detector.is_trained() else "untrained"
        }
        threat_monitoring.threat_monitor.log_prediction(prediction_data)
        
        # Log threat event if high risk
        if risk < 40:  # High threat threshold
            threat_data = {
                'threat_level': 'high' if risk < 30 else 'medium',
                'risk_score': risk,
                'action': action,
                'features': vec,
                'confidence': 1.0 - uncertainty_score
            }
            threat_monitoring.threat_monitor.log_threat_event(threat_data)
        
        # Enhanced response with robustness info
        response = {
            "token_hash": token_hash,
            "mode": "live",
            "risk": risk,
            "action": action,
            "uncertainty_score": uncertainty_score,
            "drift_detected": drift_detected,
            "response_time_ms": round(response_time * 1000, 2),
            "model_version": detector.model_version() if detector.is_trained() else "untrained",
            "robust_assessment": True
        }
        
        # Log decision
        shadow_logger.log_decision(token_hash, vec, risk, action, model_version=detector.model_version())
        
        return response
        
    except Exception as e:
        logger.exception("ml_threat_assessment failed")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/admin/ml/health")
async def admin_ml_health(x_api_key: str | None = Header(None)):
    check_api_key(x_api_key)
    try:
        detector = consensus_detector.get_detector()
        meta = detector.metadata()
        return {"trained": detector.is_trained(), "buffer_size": reservoir_buffer.size(), "meta": meta}
    except Exception as e:
        logger.exception("admin_ml_health failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/ml/retrain")
async def admin_ml_retrain(x_api_key: str | None = Header(None)):
    check_api_key(x_api_key)
    try:
        # perform robust retrain with adversarial defense
        info = robust_retrain.robust_retrain_with_adversarial()
        return {"status": "retrained", "info": info, "robust_training": True}
    except Exception as e:
        logger.exception("admin_retrain failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/ml/train-enhanced-ensemble")
async def train_enhanced_ensemble(x_api_key: str | None = Header(None)):
    """Train the enhanced ensemble detector with fair feature weighting"""
    check_api_key(x_api_key)
    try:
        # Load training data from buffer
        X = robust_retrain.load_buffer_samples(limit=1000)
        if X.size == 0:
            return {"status": "error", "message": "No training data available"}
        
        # Train enhanced ensemble
        enhanced_ensemble_detector.enhanced_detector.train(X)
        
        # Get feature analysis
        feature_analysis = enhanced_ensemble_detector.enhanced_detector.get_feature_analysis()
        
        return {
            "status": "trained",
            "enhanced_ensemble": True,
            "training_samples": len(X),
            "feature_analysis": feature_analysis,
            "fair_feature_weighting": True,
            "multi_model_consensus": True
        }
    except Exception as e:
        logger.exception("train_enhanced_ensemble failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/ml/monitoring")
async def admin_ml_monitoring(x_api_key: str | None = Header(None)):
    """Get real-time monitoring report"""
    check_api_key(x_api_key)
    try:
        monitoring_report = threat_monitoring.threat_monitor.get_monitoring_report()
        return monitoring_report
    except Exception as e:
        logger.exception("admin_monitoring failed")
        raise HTTPException(status_code=500, detail=str(e))

# Honeypot Intelligence Endpoints
@app.post("/ml/fake-score")
async def fake_ml_score(payload: ScorePayload, request: Request):
    """
    Fake ML scoring endpoint - honeypot for intelligence gathering
    """
    try:
        # Log the interaction for intelligence
        request_data = {
            "token": payload.token,
            "vector": payload.vector,
            "timestamp": payload.timestamp,
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        # Generate decoy response
        decoy_response = honeypot_intelligence.honeypot_intelligence.generate_decoy_response(
            "fake_ml_endpoint", request_data
        )
        
        return decoy_response
    except Exception as e:
        logger.exception("fake_ml_score failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/fake-crypto")
async def fake_crypto_negotiate(payload: CryptoNegotiationPayload, request: Request):
    """
    Fake crypto negotiation endpoint - honeypot for intelligence gathering
    """
    try:
        request_data = {
            "token": payload.token,
            "vector": payload.vector,
            "client_capabilities": payload.client_capabilities,
            "timestamp": payload.timestamp,
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        decoy_response = honeypot_intelligence.honeypot_intelligence.generate_decoy_response(
            "fake_crypto_service", request_data
        )
        
        return decoy_response
    except Exception as e:
        logger.exception("fake_crypto_negotiate failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/fake-health")
async def fake_admin_health(request: Request):
    """
    Fake admin health endpoint - honeypot for reconnaissance
    """
    try:
        request_data = {
            "endpoint": "/admin/fake-health",
            "method": "GET",
            "client_ip": request.client.host if request.client else "unknown",
            "timestamp": time.time()
        }
        
        decoy_response = honeypot_intelligence.honeypot_intelligence.generate_decoy_response(
            "fake_admin_panel", request_data
        )
        
        return decoy_response
    except Exception as e:
        logger.exception("fake_admin_health failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/honeypot/intelligence")
async def get_honeypot_intelligence(x_api_key: str | None = Header(None)):
    """Get honeypot intelligence report"""
    check_api_key(x_api_key)
    try:
        intelligence_report = honeypot_intelligence.honeypot_intelligence.get_intelligence_report()
        return intelligence_report
    except Exception as e:
        logger.exception("honeypot_intelligence failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/honeypot/deploy")
async def deploy_honeypot(honeypot_type: str, x_api_key: str | None = Header(None)):
    """Deploy a specific type of honeypot"""
    check_api_key(x_api_key)
    try:
        honeypot_id = honeypot_intelligence.honeypot_intelligence.deploy_honeypot(honeypot_type)
        return {"status": "deployed", "honeypot_id": honeypot_id, "type": honeypot_type}
    except Exception as e:
        logger.exception("deploy_honeypot failed")
        raise HTTPException(status_code=500, detail=str(e))

# Simple health
@app.get("/health")
async def health():
    return {"status": "ok", "service": "detector"}

# fallback root
@app.get("/")
async def root():
    return {"msg": "Threat detector (demo). See /health /ml/score /ml/observe /admin/ml/health"}

# If you want to allow running this script directly with python detector_module.py:
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DETECTOR_PORT", "8000"))
    uvicorn.run("detector_module:app", host="0.0.0.0", port=port, log_level="info")
