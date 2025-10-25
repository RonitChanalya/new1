# backend/app/routes/crypto.py
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging
import base64

from app.services import metadata_sanitizer
from app.services import metadata_leak_detector

# Try to import your key manager
try:
    from app.services import key_manager as _km_mod
    _KM = getattr(_km_mod, "km", None)
except Exception:
    _KM = None

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Try to import AEAD helper
try:
    from app.services.aead import aead_encrypt, aead_decrypt, b64_encode, b64_decode
    AEAD_AVAILABLE = True
except Exception:
    # Fallback implementation
    def aead_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> bytes:
        """Fallback AEAD encryption"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ct
    
    def aead_decrypt(key: bytes, blob: bytes, associated_data: bytes = b"") -> bytes:
        """Fallback AEAD decryption"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = blob[:12]
        ct = blob[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, associated_data)
    
    def b64_encode(b: bytes) -> str:
        return base64.b64encode(b).decode("ascii")
    
    def b64_decode(s: str) -> bytes:
        return base64.b64decode(s.encode("ascii"))
    
    AEAD_AVAILABLE = True
    logger.info("Using fallback AEAD implementation")

class HybridInitRequest(BaseModel):
    client_x25519_pub_b64: str = Field(..., min_length=1, description="Base64-encoded X25519 public key (32 bytes)")
    client_pqc_pub_b64: Optional[str] = Field(None, description="Base64-encoded PQC public key (optional if client doesn't support PQC)")

    @validator('client_x25519_pub_b64')
    def validate_x25519_key(cls, v):
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("X25519 public key must be exactly 32 bytes")
            return v
        except Exception as e:
            raise ValueError(f"Invalid X25519 public key: {str(e)}")

    @validator('client_pqc_pub_b64')
    def validate_pqc_key(cls, v):
        if v is None:
            return v
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:  # Adjust based on actual PQC algorithm
                raise ValueError("PQC public key must be exactly 32 bytes")
            return v
        except Exception as e:
            raise ValueError(f"Invalid PQC public key: {str(e)}")


router = APIRouter()

# Note: keep an explicit /crypto/keys route (you have a separate crypto_keys.py,
# but for completeness we provide get_crypto_keys here as before)


@router.get("/crypto/keys")
def get_crypto_keys():
    """
    Return server public key info (x25519 + optional PQC KEM public key).
    """
    if _KM is None:
        demo = {
            "key_id": None,
            "created_at": None,
            "x25519_pub_b64": None,
            "pqc_pub_b64": None,
            "pqc_enabled": False,
            "note": "No KeyManager available on server; run with app.services.key_manager.km"
        }
        return demo
    try:
        return _KM.export_public_keys()
    except Exception as exc:
        # log and return structured JSON error to the client
        logger.exception("KeyManager.export_public_keys() failed")
        raise HTTPException(status_code=500, detail=f"key manager error: {str(exc)}")


@router.post("/crypto/hybrid_init")
def crypto_hybrid_init(body: HybridInitRequest):
    """
    Client calls this with its public keys. Server will:
    - perform X25519 exchange to compute shared_x
    - perform PQC encapsulation to client's PQC public (if provided) and return pqc ciphertext
    - return server x25519 pub + the pqc ciphertext (client decapsulates) so both sides can derive the same symmetric key
    """
    if _KM is None:
        logger.error("KeyManager not available for hybrid_init request")
        raise HTTPException(status_code=503, detail="KeyManager not available on server")

    try:
        # Validate client X25519 public key
        try:
            client_x25519_bytes = base64.b64decode(body.client_x25519_pub_b64)
            if len(client_x25519_bytes) != 32:
                raise ValueError("X25519 public key must be 32 bytes")
        except Exception as e:
            logger.warning("Invalid client X25519 public key: %s", str(e))
            raise HTTPException(status_code=400, detail="Invalid client X25519 public key")

        # Validate client PQC public key if provided
        if body.client_pqc_pub_b64:
            try:
                client_pqc_bytes = base64.b64decode(body.client_pqc_pub_b64)
                if len(client_pqc_bytes) != 32:  # Adjust based on actual PQC algorithm
                    raise ValueError("PQC public key must be 32 bytes")
            except Exception as e:
                logger.warning("Invalid client PQC public key: %s", str(e))
                raise HTTPException(status_code=400, detail="Invalid client PQC public key")

        # Perform hybrid key exchange
        shared_material, pqc_ct = _KM.derive_shared_secret_server_side(
            client_x25519_pub_b64=body.client_x25519_pub_b64,
            client_pqc_pub_b64=body.client_pqc_pub_b64,
        )

        # Server also derives a symmetric key for its own use (won't send it to client)
        server_sym = _KM.derive_symmetric_key(shared_material)

        # Build response with server public keys and PQC ciphertext
        server_keys = _KM.export_public_keys()
        resp = {
            "key_id": _KM.key_id,
            "x25519_pub_b64": server_keys.get("x25519_pub_b64"),
            "pqc_ct_b64": base64.b64encode(pqc_ct).decode("ascii") if pqc_ct is not None else None,
            "pqc_enabled": server_keys.get("pqc_enabled", False),
            "pqc_kem": server_keys.get("pqc_kem"),
        }

        logger.info("Hybrid key exchange successful for key_id=%s, pqc_enabled=%s",
                    _KM.key_id, resp["pqc_enabled"])
        return resp

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception("Hybrid key exchange failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Hybrid key exchange failed: {str(e)}")


class HybridSendRequest(BaseModel):
    """Request model for hybrid-enabled message sending"""
    token: str = Field(..., min_length=1, description="Opaque conversation / message token")
    message_b64: str = Field(..., min_length=1, description="Base64-encoded plaintext message")
    ttl_seconds: int = Field(..., gt=0, description="Requested TTL in seconds")
    client_x25519_pub_b64: str = Field(..., min_length=1, description="Client X25519 public key")
    client_pqc_pub_b64: Optional[str] = Field(None, description="Client PQC public key (optional)")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")

    @validator('client_x25519_pub_b64')
    def validate_x25519_key(cls, v):
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("X25519 public key must be exactly 32 bytes")
            return v
        except Exception as e:
            raise ValueError(f"Invalid X25519 public key: {str(e)}")

    @validator('client_pqc_pub_b64')
    def validate_pqc_key(cls, v):
        if v is None:
            return v
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("PQC public key must be exactly 32 bytes")
            return v
        except Exception as e:
            raise ValueError(f"Invalid PQC public key: {str(e)}")


class HybridSendResponse(BaseModel):
    """Response model for hybrid-enabled message sending"""
    status: str = Field(..., description="stored | blocked | require_reauth | pending_approval")
    risk: int = Field(..., ge=0, le=100, description="Risk score (0..100)")
    policy: str = Field(..., description="allow | require_reauth | block | pending_approval")
    message: Optional[str] = Field(None, description="Human-friendly explanation")
    key_id: str = Field(..., description="Server key ID used for encryption")
    encrypted_message_b64: Optional[str] = Field(None, description="Server-encrypted message (if stored)")


@router.post("/crypto/send", response_model=HybridSendResponse)
def crypto_hybrid_send(request: Request, body: HybridSendRequest):
    """
    Hybrid-enabled message sending with E2E encryption.

    This endpoint:
    1. Performs hybrid key exchange (X25519 + PQC)
    2. Encrypts the plaintext message using derived symmetric key (AEAD)
    3. Applies ML risk assessment and policy enforcement
    4. Stores encrypted message if approved
    """
    if _KM is None:
        logger.error("KeyManager not available for hybrid send")
        raise HTTPException(status_code=503, detail="KeyManager not available on server")

    try:
        # Step 1: Perform hybrid key exchange
        shared_material, pqc_ct = _KM.derive_shared_secret_server_side(
            client_x25519_pub_b64=body.client_x25519_pub_b64,
            client_pqc_pub_b64=body.client_pqc_pub_b64,
        )

        # Step 2: Derive symmetric key for message encryption
        symmetric_key = _KM.derive_symmetric_key(shared_material)  # expected 16/24/32 bytes (HKDF default 32)

        # Step 3: Decode plaintext
        try:
            plaintext_message = base64.b64decode(body.message_b64)
        except Exception as e:
            logger.warning("Failed to decode message base64: %s", str(e))
            raise HTTPException(status_code=400, detail="Invalid message base64")

        # --- AEAD encryption (AES-GCM) ---
        if not AEAD_AVAILABLE:
            logger.error("AEAD helper not available; encryption cannot proceed")
            raise HTTPException(status_code=500, detail="Encryption helper unavailable")

        # Build associated data (bind token and minimal sanitized metadata to ciphertext)
        sanitized_metadata_for_aad = {
            "padded_size": None,
            "dest_count": None
        }
        # We'll sanitize metadata further down; use provided metadata minimally here
        try:
            sanitized_metadata_for_aad["padded_size"] = int(body.metadata.get("padded_size", len(plaintext_message)))
        except Exception:
            sanitized_metadata_for_aad["padded_size"] = len(plaintext_message)
        try:
            sanitized_metadata_for_aad["dest_count"] = int(body.metadata.get("dest_count", 1))
        except Exception:
            sanitized_metadata_for_aad["dest_count"] = 1

        assoc_parts = [
            body.token,
            str(_KM.key_id),
            str(sanitized_metadata_for_aad["padded_size"]),
            str(sanitized_metadata_for_aad["dest_count"])
        ]
        associated_data = "|".join(assoc_parts).encode("utf-8")

        try:
            encrypted_blob = aead_encrypt(symmetric_key, plaintext_message, associated_data=associated_data)
        except Exception as e:
            logger.exception("AEAD encryption failed: %s", str(e))
            raise HTTPException(status_code=500, detail="Encryption failure")

        encrypted_message = bytes(encrypted_blob)
        # --- end AEAD encryption ---

        # Step 4: Detect and sanitize metadata leaks
        metadata = body.metadata or {}

        # Detect metadata leaks using AI
        leak_detection_result = metadata_leak_detector.detect_metadata_leaks(metadata)
        leak_detected = leak_detection_result.get('leak_detected', False)
        leak_risk_score = leak_detection_result.get('risk_score', 0.0)
        leak_types = leak_detection_result.get('leak_types', [])

        logger.info("Hybrid send metadata leak detection: detected=%s, risk=%.2f, types=%s",
                    leak_detected, leak_risk_score, leak_types)

        # Sanitize metadata to eliminate leaks
        sanitized_metadata, sanitization_report = metadata_sanitizer.sanitize_metadata(metadata)

        logger.info("Hybrid send metadata sanitization: original_fields=%d, sanitized_fields=%d, removed=%s",
                    sanitization_report.get('original_fields', 0),
                    sanitization_report.get('sanitized_fields', 0),
                    sanitization_report.get('removed_fields', []))

        # Step 5: Build ML vector from sanitized metadata
        vector = [
            float(sanitized_metadata.get("padded_size", len(plaintext_message))),
            float(sanitized_metadata.get("interval", 0.0)),
            float(sanitized_metadata.get("dest_count", 1.0)),
            1.0 if sanitized_metadata.get("new_device") else 0.0
        ]

        # Import ML and policy modules
        from app.services import ml_adapter as ml_module
        from app.services import policy as policy_module

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

        # Step 6: Adjust risk score based on metadata leak detection
        if leak_detected:
            # Increase risk if metadata leaks detected
            leak_adjustment = int(leak_risk_score * 30)  # Up to 30 points adjustment
            risk = min(100, base_risk + leak_adjustment)
            logger.info("Hybrid send risk adjusted for metadata leaks: base=%d, adjustment=%d, final=%d",
                        base_risk, leak_adjustment, risk)
        else:
            risk = base_risk

        # Step 7: Apply policy decision using sanitized metadata
        client_ip = request.client.host if request.client else None
        metadata_summary = {
            "padded_size": len(plaintext_message),
            "dest_count": sanitized_metadata.get("dest_count", 1),
            "exception_flag": bool(sanitized_metadata.get("exception_flag", False)),
            "leak_detected": leak_detected,
            "leak_types": leak_types,
            "sanitization_applied": sanitization_report.get("sanitization_applied", False)
        }

        decision = policy_module.decide_action(
            risk_score=risk,
            token=body.token,
            metadata_summary=metadata_summary,
            client_ip=client_ip
        )

        action = decision.get("action")
        policy = decision.get("policy")
        enforced = decision.get("enforced", True)
        reason = decision.get("reason", "")

        # Step 8: Handle policy decision
        if not enforced:
            # Shadow mode - simulate but don't store
            logger.info("Shadow-mode: hybrid send token=%s risk=%s policy=%s", body.token, risk, policy)
            return HybridSendResponse(
                status="stored",
                risk=risk,
                policy=policy,
                message=f"Shadow-mode: {reason}",
                key_id=_KM.key_id,
                encrypted_message_b64=None
            )

        if action == "block":
            logger.info("Blocking hybrid send token=%s risk=%s", body.token, risk)
            return HybridSendResponse(
                status="blocked",
                risk=risk,
                policy="block",
                message="Blocked due to high risk",
                key_id=_KM.key_id,
                encrypted_message_b64=None
            )

        if action == "require_reauth":
            logger.info("Require reauth for hybrid send token=%s risk=%s", body.token, risk)
            return HybridSendResponse(
                status="require_reauth",
                risk=risk,
                policy="require_reauth",
                message="Reauthentication required",
                key_id=_KM.key_id,
                encrypted_message_b64=None
            )

        if action == "pending_approval":
            logger.info("Pending approval for hybrid send token=%s risk=%s", body.token, risk)
            return HybridSendResponse(
                status="pending_approval",
                risk=risk,
                policy="pending_approval",
                message="Pending admin approval",
                key_id=_KM.key_id,
                encrypted_message_b64=None
            )

        # action == "allow" -> store encrypted message
        try:
            from app.services import storage as storage_module
            storage_module.storage.put(body.token, encrypted_message, body.ttl_seconds)

            logger.info("Stored hybrid encrypted message token=%s ttl=%s risk=%s",
                        body.token, body.ttl_seconds, risk)

            # Enhanced response with metadata leak information
            response_message = f"Message encrypted and stored; will expire in {body.ttl_seconds}s"
            if leak_detected:
                response_message += f" (metadata leaks detected and sanitized: {', '.join(leak_types)})"
            elif sanitization_report.get("sanitization_applied", False):
                response_message += " (metadata sanitized for security)"

            return HybridSendResponse(
                status="stored",
                risk=risk,
                policy="allow",
                message=response_message,
                key_id=_KM.key_id,
                encrypted_message_b64=base64.b64encode(encrypted_message).decode("ascii")
            )

        except Exception as e:
            logger.exception("Failed to store hybrid encrypted message for token=%s", body.token)
            raise HTTPException(status_code=500, detail="Internal storage error")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Hybrid send failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Hybrid send failed: {str(e)}")
