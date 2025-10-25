# backend/app/routes/fetch.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import base64
import logging
import time

from app.schemas import FetchResponse
from app.services import storage as storage_module

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()


@router.get("/fetch/{token}", response_model=FetchResponse)
def get_fetch(token: str):
    """
    Fetch the ciphertext for a given token if it exists and hasn't expired.
    Returns:
      - ciphertext_b64
      - ttl_remaining (seconds)
      - message_state: "available" | "expired"
    """
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    entry = storage_module.storage.get(token)
    if entry is None:
        # No entry or expired
        logger.info("Fetch requested for missing/expired token=%s", token)
        raise HTTPException(status_code=404, detail="No message")

    # entry contains ciphertext (bytes), expire_at, read flag
    ciphertext = entry.get("ciphertext")
    expire_at = entry.get("expire_at", 0)
    now = time.time()
    ttl_remaining = max(0, int(expire_at - now))

    # Safety: if TTL reached zero (race), remove and return 404
    if ttl_remaining == 0:
        try:
            storage_module.storage.mark_read_and_delete(token)
        except Exception:
            logger.exception("Error deleting expired token=%s", token)
        raise HTTPException(status_code=404, detail="No message")

    # encode base64 for transport
    try:
        ciphertext_b64 = base64.b64encode(ciphertext).decode("utf-8")
    except Exception:
        logger.exception("Failed to base64-encode ciphertext for token=%s", token)
        raise HTTPException(status_code=500, detail="Internal error")

    resp = {
        "ciphertext_b64": ciphertext_b64,
        "ttl_remaining": ttl_remaining,
        "message_state": "available",
    }
    return JSONResponse(status_code=200, content=resp)
