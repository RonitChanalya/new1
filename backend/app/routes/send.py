# backend/app/routes/send.py
from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import ValidationError
from typing import Optional
import base64
import logging
import time

from app.schemas import SendRequest, SendResponse
from app.services import storage as storage_module
from app.services import key_manager as km_module
from app.services import ml_adapter as ml_module
from app.services import policy as policy_module
from app.services import metadata_sanitizer
from app.services import metadata_leak_detector

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()


def _build_vector_from_metadata(metadata: Optional[dict]) -> list:
    """
    Build a numeric vector from metadata for ML scoring.
    Keep it minimal and anonymized. Expected layout:
      [padded_size, interval, dest_count, device_change_flag]
    'dest_count' may not be available from client; default to 1.
    """
    if not metadata:
        return [0.0, 0.0, 1.0, 0.0]
    padded_size = float(metadata.get("padded_size") or 0.0)
    interval = float(metadata.get("interval") or 0.0)
    dest_count = float(metadata.get("dest_count") or 1.0)
    device_change = 1.0 if metadata.get("new_device") else 0.0
    return [padded_size, interval, dest_count, device_change]


@router.post("/send", response_model=SendResponse, status_code=200)
def post_send(request: Request, body: dict):
    """
    Accept an encrypted message payload and enforce ML + policy decisions.

    Expected JSON (SendRequest model):
      token, ciphertext_b64, ttl_seconds, metadata (optional)

    Returns SendResponse:
      status (stored|blocked|require_reauth|pending_approval), risk (0..100), policy, message
    """
    # parse & validate via pydantic
    try:
        req = SendRequest.parse_obj(body)
    except ValidationError as ve:
        logger.warning("Invalid send request: %s", ve)
        raise HTTPException(status_code=400, detail="Invalid request payload")

    token = req.token
    ttl = int(req.ttl_seconds)
    metadata = req.metadata.dict() if req.metadata else {}
    # extract client IP (best-effort, may be proxied)
    client_ip = request.client.host if request.client else None

    # decode ciphertext to validate base64
    try:
        ciphertext = base64.b64decode(req.ciphertext_b64)
    except Exception:
        logger.warning("Failed to decode base64 ciphertext for token=%s", token)
        raise HTTPException(status_code=400, detail="Invalid ciphertext base64")

    # Step 1: Detect metadata leaks using AI
    leak_detection_result = metadata_leak_detector.detect_metadata_leaks(metadata)
    leak_detected = leak_detection_result.get('leak_detected', False)
    leak_risk_score = leak_detection_result.get('risk_score', 0.0)
    leak_types = leak_detection_result.get('leak_types', [])
    
    logger.info("Metadata leak detection: detected=%s, risk=%.2f, types=%s", 
               leak_detected, leak_risk_score, leak_types)
    
    # Step 2: Sanitize metadata to eliminate leaks
    sanitized_metadata, sanitization_report = metadata_sanitizer.sanitize_metadata(metadata)
    
    logger.info("Metadata sanitization: original_fields=%d, sanitized_fields=%d, removed=%s",
               sanitization_report.get('original_fields', 0),
               sanitization_report.get('sanitized_fields', 0),
               sanitization_report.get('removed_fields', []))
    
    # Step 3: Build ML vector from sanitized metadata
    vector = _build_vector_from_metadata(sanitized_metadata)
    
    # Step 4: Enhanced ML scoring with leak detection
    ml = getattr(ml_module, "ml", None)
    if ml is None:
        logger.warning("ML adapter not available; using conservative fallback risk=50")
        base_risk = 50
    else:
        try:
            base_risk = int(ml.score(vector))
        except Exception:
            logger.exception("ML scoring failed; defaulting risk=50")
            base_risk = 50
    
    # Step 5: Adjust risk score based on metadata leak detection
    if leak_detected:
        # Increase risk if metadata leaks detected
        leak_adjustment = int(leak_risk_score * 30)  # Up to 30 points adjustment
        risk = min(100, base_risk + leak_adjustment)
        logger.info("Risk adjusted for metadata leaks: base=%d, adjustment=%d, final=%d",
                   base_risk, leak_adjustment, risk)
    else:
        risk = base_risk

    # Prepare metadata summary for policy using sanitized metadata
    metadata_summary = {
        "padded_size": sanitized_metadata.get("padded_size"),
        "dest_count": sanitized_metadata.get("dest_count") or 1,
        "exception_flag": bool(sanitized_metadata.get("exception_flag", False)),
        "leak_detected": leak_detected,
        "leak_types": leak_types,
        "sanitization_applied": sanitization_report.get("sanitization_applied", False)
    }

    # Decide policy
    decision = policy_module.decide_action(risk_score=risk, token=token, metadata_summary=metadata_summary, client_ip=client_ip)
    action = decision.get("action")
    policy = decision.get("policy")
    enforced = decision.get("enforced", True)
    reason = decision.get("reason", "")

    # If not enforced (shadow / canary), return simulated policy but do not block.
    if not enforced:
        # If shadow/canary, we still store by default (safe path)
        # Store ciphertext and generate session key to allow frontend progress
        try:
            storage_module.storage.put(token, ciphertext, ttl)
            key_bytes = km_module.km.generate_session(token, ttl)
            # key not returned in production route; frontend uses secure exchange
            logger.info("Shadow-mode: stored token=%s risk=%s policy=%s", token, risk, policy)
            return SendResponse(status="stored", risk=risk, policy=policy, message=f"Shadow-mode: {reason}")
        except Exception:
            logger.exception("Failed to store in shadow-mode")
            raise HTTPException(status_code=500, detail="Internal error")

    # Enforced decision handling
    if action == "block":
        # Block outright
        logger.info("Blocking send token=%s risk=%s", token, risk)
        return SendResponse(status="blocked", risk=risk, policy="block", message="Blocked due to high risk")

    if action == "require_reauth":
        # Indicate require reauth; frontend should trigger MFA and retry.
        logger.info("Require reauth for token=%s risk=%s", token, risk)
        return SendResponse(status="require_reauth", risk=risk, policy="require_reauth", message="Reauthentication required")

    if action == "pending_approval":
        # Queue for approval (for this prototype we treat as pending and do not store)
        logger.info("Pending approval for token=%s risk=%s", token, risk)
        # For an advanced flow, you might store the ciphertext in a special queue; here we leave it pending.
        return SendResponse(status="pending_approval", risk=risk, policy="pending_approval", message="Pending admin approval")

    # action == "allow"
    try:
        # store ciphertext ephemeral
        storage_module.storage.put(token, ciphertext, ttl)
        # generate ephemeral session key tied to token
        key_bytes = km_module.km.generate_session(token, ttl)
        # DO NOT return key in production. For demo, frontend might call /key/{token} if enabled.
        logger.info("Stored token=%s ttl=%s risk=%s", token, ttl, risk)
        
        # Enhanced response with metadata leak information
        response_message = f"Stored; will expire in {ttl}s"
        if leak_detected:
            response_message += f" (metadata leaks detected and sanitized: {', '.join(leak_types)})"
        elif sanitization_report.get("sanitization_applied", False):
            response_message += " (metadata sanitized for security)"
        
        return SendResponse(status="stored", risk=risk, policy="allow", message=response_message)
    except Exception:
        logger.exception("Failed to store ciphertext for token=%s", token)
        raise HTTPException(status_code=500, detail="Internal storage error")
