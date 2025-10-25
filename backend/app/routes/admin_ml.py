# backend/app/routes/admin_ml.py
from typing import Optional, Dict, Any
import os
import logging

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse

from app.services import ml_adapter as ml_module
from app.services import policy as policy_module
from app.services import storage as storage_module
from app.services import metadata_leak_detector, metadata_sanitizer

from app.services.auth_helpers import check_api_key

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/admin")

# Admin API key env var (supports comma-separated keys)
ADMIN_API_ENV = "ADMIN_API_KEY"


def _require_admin_key(api_key_header: Optional[str]):
    """
    Require admin authentication using API key(s) defined in ADMIN_API_KEY env var.
    Uses constant-time comparison and supports multiple comma-separated keys.
    In production, replace with mTLS/JWT/OAuth where possible.
    """
    if not os.environ.get(ADMIN_API_ENV, "").strip():
        logger.error("ADMIN_API_KEY not configured; admin endpoints disabled.")
        raise HTTPException(status_code=503, detail="Admin endpoints unavailable.")

    if not check_api_key(api_key_header, ADMIN_API_ENV):
        logger.warning("Unauthorized admin access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized.")


@router.get("/ml/health")
def admin_ml_health(x_api_key: Optional[str] = Header(None)):
    """
    Get current ML adapter health (buffer size, model status, etc.)
    """
    _require_admin_key(x_api_key)

    ml = getattr(ml_module, "ml", None)
    if ml is None:
        raise HTTPException(status_code=503, detail="ML adapter unavailable.")

    try:
        health = ml.health()
    except Exception:
        logger.exception("Failed to fetch ML health.")
        raise HTTPException(status_code=500, detail="ML health unavailable.")

    return JSONResponse(status_code=200, content={"status": "ok", "ml_health": health})


@router.post("/ml/retrain")
def admin_ml_retrain(x_api_key: Optional[str] = Header(None)):
    """
    Force retrain of the ML model on current buffer.
    """
    _require_admin_key(x_api_key)

    ml = getattr(ml_module, "ml", None)
    if ml is None:
        raise HTTPException(status_code=503, detail="ML adapter unavailable.")

    try:
        success = ml.force_retrain()
        if not success:
            return JSONResponse(status_code=200, content={"status": "not_enough_data"})
        return JSONResponse(status_code=200, content={"status": "retrained"})
    except Exception:
        logger.exception("Admin ML retrain failed.")
        raise HTTPException(status_code=500, detail="Retrain failed.")


@router.get("/policy/status")
def admin_policy_status(x_api_key: Optional[str] = Header(None)):
    """
    Retrieve current policy thresholds and status.
    """
    _require_admin_key(x_api_key)

    try:
        st = policy_module.status()
    except Exception:
        logger.exception("Failed to fetch policy status.")
        raise HTTPException(status_code=500, detail="Policy status unavailable.")

    return JSONResponse(status_code=200, content={"status": "ok", "policy": st})


@router.post("/policy/thresholds")
def admin_policy_set_thresholds(
    allow: Optional[int] = None,
    reauth: Optional[int] = None,
    x_api_key: Optional[str] = Header(None)
):
    """
    Update policy thresholds dynamically.
    """
    _require_admin_key(x_api_key)

    try:
        policy_module.set_thresholds(allow=allow, reauth=reauth)
    except Exception:
        logger.exception("Failed to set policy thresholds.")
        raise HTTPException(status_code=500, detail="Threshold update failed.")

    return JSONResponse(status_code=200, content={"status": "ok", "allow": allow, "reauth": reauth})


@router.get("/audit/read")
def admin_read_audit(limit: Optional[int] = 100, x_api_key: Optional[str] = Header(None)):
    """
    Read recent audit log lines (from POLICY_AUDIT_LOG_PATH).
    Returns last N lines as JSON.
    """
    _require_admin_key(x_api_key)

    try:
        audit_path = policy_module.AUDIT_LOG_PATH
        with open(audit_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = [line.strip() for line in lines[-limit:]]
    except FileNotFoundError:
        entries = []
    except Exception:
        logger.exception("Failed to read audit log.")
        raise HTTPException(status_code=500, detail="Failed to read audit log.")

    return JSONResponse(status_code=200, content={"status": "ok", "entries": entries})


@router.get("/forensic/status")
def admin_forensic_status(x_api_key: Optional[str] = Header(None)):
    """
    Get forensic protection system status.
    """
    _require_admin_key(x_api_key)

    try:
        forensic_status = storage_module.storage.get_forensic_status()
        return JSONResponse(status_code=200, content={"status": "ok", "forensic": forensic_status})
    except Exception:
        logger.exception("Failed to fetch forensic status.")
        raise HTTPException(status_code=500, detail="Forensic status unavailable.")


@router.post("/forensic/cleanup")
def admin_forensic_cleanup(x_api_key: Optional[str] = Header(None)):
    """
    Force immediate secure cleanup of all stored messages.
    """
    _require_admin_key(x_api_key)

    try:
        deleted_count = storage_module.storage.force_secure_cleanup()
        return JSONResponse(status_code=200, content={"status": "ok", "deleted_count": deleted_count})
    except Exception:
        logger.exception("Forensic cleanup failed.")
        raise HTTPException(status_code=500, detail="Forensic cleanup failed.")


@router.get("/forensic/audit-integrity")
def admin_forensic_audit_integrity(x_api_key: Optional[str] = Header(None)):
    """
    Verify audit log integrity and tamper detection.
    """
    _require_admin_key(x_api_key)

    try:
        integrity_result = storage_module.storage.verify_audit_integrity()
        return JSONResponse(status_code=200, content={"status": "ok", "integrity": integrity_result})
    except Exception:
        logger.exception("Audit integrity verification failed.")
        raise HTTPException(status_code=500, detail="Audit integrity verification failed.")


@router.get("/metadata/leak-detection-stats")
def admin_metadata_leak_detection_stats(x_api_key: Optional[str] = Header(None)):
    """
    Get metadata leak detection statistics.
    """
    _require_admin_key(x_api_key)

    try:
        stats = metadata_leak_detector.get_detection_stats()
        return JSONResponse(status_code=200, content={"status": "ok", "leak_detection": stats})
    except Exception:
        logger.exception("Failed to fetch metadata leak detection stats.")
        raise HTTPException(status_code=500, detail="Metadata leak detection stats unavailable.")


@router.get("/metadata/sanitization-stats")
def admin_metadata_sanitization_stats(x_api_key: Optional[str] = Header(None)):
    """
    Get metadata sanitization statistics.
    """
    _require_admin_key(x_api_key)

    try:
        stats = metadata_sanitizer.get_sanitization_stats()
        return JSONResponse(status_code=200, content={"status": "ok", "sanitization": stats})
    except Exception:
        logger.exception("Failed to fetch metadata sanitization stats.")
        raise HTTPException(status_code=500, detail="Metadata sanitization stats unavailable.")


@router.post("/metadata/test-sanitization")
def admin_test_metadata_sanitization(test_metadata: Dict[str, Any], x_api_key: Optional[str] = Header(None)):
    """
    Test metadata sanitization on provided metadata.
    """
    _require_admin_key(x_api_key)

    try:
        # Test leak detection
        leak_result = metadata_leak_detector.detect_metadata_leaks(test_metadata)

        # Test sanitization
        sanitized_metadata, sanitization_report = metadata_sanitizer.sanitize_metadata(test_metadata)

        return JSONResponse(status_code=200, content={
            "status": "ok",
            "original_metadata": test_metadata,
            "leak_detection": leak_result,
            "sanitized_metadata": sanitized_metadata,
            "sanitization_report": sanitization_report
        })
    except Exception:
        logger.exception("Metadata sanitization test failed.")
        raise HTTPException(status_code=500, detail="Metadata sanitization test failed.")
