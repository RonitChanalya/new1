# backend/app/routes/ml_score.py
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
import logging
import os
import time
from typing import Optional

from app.services.auth_helpers import check_api_key
import os

ML_API_ENV = "ML_API_KEY"

from app.schemas import MLObserveRequest
from app.services import ml_adapter as ml_module

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()

# Admin API key to protect synchronous scoring endpoint (set in env)
ML_API_KEY = os.environ.get("ML_API_KEY", None)


# def _require_api_key(api_key_header: Optional[str]):
#     """
#     Simple API key check. In production, use mutual TLS or OAuth between services.
#     """
#     if ML_API_KEY is None:
#         # If not configured, disallow scoring to avoid accidental exposure
#         logger.error("ML_API_KEY not configured; synchronous scoring disabled")
#         raise HTTPException(status_code=503, detail="Service unavailable")
#     if not api_key_header or api_key_header != ML_API_KEY:
#         logger.warning("Unauthorized ml/score access attempt")
#         raise HTTPException(status_code=401, detail="Unauthorized")

def _require_api_key(api_key_header: Optional[str]):
    """
    Check ML API key using constant-time comparison.
    If ML_API_KEY env var is missing, disable endpoint (503).
    In production, prefer mTLS/JWT/OAuth for inter-service auth.
    """
    if not os.environ.get(ML_API_ENV, "").strip():
        logger.error("ML_API_KEY not configured; synchronous scoring disabled.")
        raise HTTPException(status_code=503, detail="Service unavailable")

    if not check_api_key(api_key_header, ML_API_ENV):
        logger.warning("Unauthorized ml/score access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized.")


@router.post("/ml/score")
def post_ml_score(body: dict, x_api_key: Optional[str] = Header(None)):
    """
    Synchronous scoring endpoint (protected).

    Request body: same as MLObserveRequest:
      {
        "token": "opaque",
        "vector": [padded_size, interval, dest_count, device_change_flag, ...],
        "timestamp": optional
      }

    Response:
      { "status": "ok", "risk": <int 0..100>, "simulated": <bool if in shadow>, "ts": <epoch> }
    """
    # Auth
    _require_api_key(x_api_key)

    # Validate payload
    try:
        req = MLObserveRequest.parse_obj(body)
    except Exception:
        logger.warning("Invalid ml/score payload")
        raise HTTPException(status_code=400, detail="Invalid payload")

    vector = req.vector
    token = req.token
    ts = req.timestamp or time.time()

    ml = getattr(ml_module, "ml", None)
    if ml is None:
        logger.error("ML adapter not available for scoring")
        raise HTTPException(status_code=503, detail="ML unavailable")

    try:
        # Compute risk (0..100). The ML adapter should be production-grade (IsolationForest).
        risk = int(ml.score(vector))
    except Exception:
        logger.exception("ML scoring failed")
        raise HTTPException(status_code=500, detail="Scoring error")

    # Optionally record the observation (adapter may already do this internally)
    try:
        ml.add_observation(vector)
    except Exception:
        # non-fatal; continue
        logger.exception("Failed to add observation to ML buffer (continuing)")

    # Simulated flag: if ML adapter reports health/trained False, we note it
    simulated = False
    try:
        health = ml.health()
        if not health.get("trained", False):
            simulated = True
    except Exception:
        simulated = True

    resp = {
        "status": "ok",
        "risk": risk,
        "simulated": simulated,
        "ts": int(ts),
    }
    return JSONResponse(status_code=200, content=resp)
