# backend/app/routes/read.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.services import storage as storage_module
from app.services import key_manager as km_module
from app.schemas import ReadResponse

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter()


@router.post("/read/{token}", response_model=ReadResponse)
def post_read(token: str):
    """
    Mark a message as read and delete it from ephemeral storage.
    Also revoke any associated ephemeral session key.
    """
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    try:
        deleted = storage_module.storage.mark_read_and_delete(token)
    except Exception:
        logger.exception("Error while deleting token=%s", token)
        raise HTTPException(status_code=500, detail="Internal error")

    # Revoke associated key (best-effort)
    try:
        km_module.km.revoke_key(token)
    except Exception:
        logger.exception("Failed to revoke key for token=%s (continuing)", token)

    if not deleted:
        raise HTTPException(status_code=404, detail="No message")

    return JSONResponse(status_code=200, content={"status": "deleted"})
