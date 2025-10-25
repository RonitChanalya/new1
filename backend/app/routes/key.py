# backend/app/routes/key.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import base64
import logging

from app.services import key_manager as km_module
from app.schemas import KeyResponse

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()


@router.get("/key/{token}", response_model=KeyResponse)
def get_key(token: str):
    """
    Demo-only: return the base64-encoded ephemeral session key for the given token.
    IMPORTANT: This endpoint should be disabled in production. Use secure key exchange instead.
    """
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    try:
        key_b64 = km_module.km.key_b64(token)
    except Exception:
        logger.exception("Error retrieving key for token=%s", token)
        raise HTTPException(status_code=500, detail="Internal error")

    if key_b64 is None:
        raise HTTPException(status_code=404, detail="Key not available")

    return JSONResponse(status_code=200, content={"key_b64": key_b64})
