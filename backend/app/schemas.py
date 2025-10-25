# backend/app/schemas.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, constr, conint


# ---------- Metadata and small helpers ----------

class Metadata(BaseModel):
    padded_size: Optional[int] = Field(None, description="Length of payload after padding (bytes)")
    interval: Optional[float] = Field(None, description="Seconds since sender's last message (approx)")
    new_device: Optional[bool] = Field(False, description="True if device fingerprint changed")
    exception_flag: Optional[bool] = Field(False, description="True if sender marked message as exceptional")
    # Note: do NOT include raw device identifiers or plain timestamps here.


# ---------- Send endpoint ----------

class SendRequest(BaseModel):
    token: constr(strip_whitespace=True, min_length=1) = Field(..., description="Opaque conversation / message token")
    ciphertext_b64: constr(strip_whitespace=True, min_length=1) = Field(..., description="Base64-encoded ciphertext")
    ttl_seconds: conint(gt=0) = Field(..., description="Requested TTL in seconds")
    metadata: Optional[Metadata] = Field(default_factory=Metadata)


class SendResponse(BaseModel):
    status: constr(strip_whitespace=True) = Field(..., description="stored | blocked | require_reauth | pending_approval")
    risk: conint(ge=0, le=100) = Field(..., description="Risk score (0..100); lower may mean higher risk depending on ML scale")
    policy: constr(strip_whitespace=True) = Field(..., description="allow | require_reauth | block | pending_approval")
    message: Optional[str] = Field(None, description="Human-friendly short explanation")


# ---------- Fetch endpoint ----------

class FetchResponse(BaseModel):
    ciphertext_b64: constr(strip_whitespace=True, min_length=1) = Field(..., description="Base64-encoded ciphertext")
    ttl_remaining: conint(ge=0) = Field(..., description="Seconds remaining before server TTL expiry")
    message_state: constr(strip_whitespace=True) = Field(..., description="available | expired")


# ---------- Read endpoint ----------

class ReadResponse(BaseModel):
    status: constr(strip_whitespace=True) = Field(..., description="deleted")


# ---------- Key endpoint (demo-only) ----------

class KeyResponse(BaseModel):
    key_b64: constr(strip_whitespace=True, min_length=1) = Field(..., description="Base64-encoded ephemeral key (demo only)")


# ---------- ML observe ----------

class MLObserveRequest(BaseModel):
    token: constr(strip_whitespace=True, min_length=1)
    vector: List[float] = Field(..., description="Numerical feature vector for ML (padded_size, interval, dest_count, device_change_flag, ...)")
    timestamp: Optional[float] = Field(None, description="Optional client timestamp; server may ignore")


class MLObserveResponse(BaseModel):
    status: constr(strip_whitespace=True) = Field("ok")


# ---------- Approval endpoints (optional) ----------

class ApprovalRequest(BaseModel):
    token: constr(strip_whitespace=True, min_length=1)
    reason: Optional[str] = Field(None, description="Short reason for requesting an exception (user-provided)")


class ApprovalResponse(BaseModel):
    request_id: constr(strip_whitespace=True, min_length=1)
    status: constr(strip_whitespace=True) = Field(..., description="pending | approved | denied")


# ---------- Generic error shape (optional helper) ----------

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error detail message")
