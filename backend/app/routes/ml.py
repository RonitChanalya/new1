# backend/app/routes/ml.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import time
from typing import Optional

from app.schemas import MLObserveRequest, MLObserveResponse
from app.services import ml_adapter as ml_module

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()


@router.post("/ml/observe", response_model=MLObserveResponse)
def post_ml_observe(body: dict):
    """
    Accept an anonymized observation vector for ML ingestion.

    Expected payload (MLObserveRequest):
      {
        "token": "<opaque token>",     # optional but helpful (will be hashed in ML logs if needed)
        "vector": [padded_size, interval, dest_count, device_change_flag, ...],
        "timestamp": 169...
      }

    Behavior:
      - Adds observation to ML buffer via ml.add_observation(vector)
      - Returns { "status": "ok" } on success

    Notes:
      - This endpoint should never receive raw user-identifying data (IP/device IDs/plaintext).
      - In many deployments, the backend will call ML adapters directly (internal), and frontend should not call this endpoint.
    """
    # Validate and parse with pydantic schema for clarity
    try:
        req = MLObserveRequest.parse_obj(body)
    except Exception:
        logger.warning("Invalid ML observe payload")
        raise HTTPException(status_code=400, detail="Invalid payload")

    vector = req.vector
    token = req.token  # opaque; ML adapter should not record raw token
    # timestamp optional
    ts = req.timestamp or time.time()

    ml = getattr(ml_module, "ml", None)
    if ml is None:
        logger.warning("ML adapter not available; dropping observation")
        # still return OK to avoid upstream failures; alternatively return 503
        return JSONResponse(status_code=200, content={"status": "ok"})

    try:
        # Add observation for training/analysis
        ml.add_observation(vector)
    except Exception:
        logger.exception("Failed to add ML observation")
        # non-fatal in pipelines; return 500 if you want strictness
        raise HTTPException(status_code=500, detail="ML ingestion error")

    return JSONResponse(status_code=200, content={"status": "ok"})
