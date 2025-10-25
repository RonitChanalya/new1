# backend/app/services/policy.py
"""
Production-grade policy engine.

Responsibilities:
- Map ML risk scores (0..100) to actions: ALLOW | REQUIRE_REAUTH | BLOCK | PENDING_APPROVAL
- Support shadow mode (compute decision but don't enforce)
- Support canary fraction (apply policy only to X% of requests)
- Emit secure audit records (no plaintext message content)
- Provide helper functions for external use:
    decide_action(risk: int, token: str, metadata: dict, client_ip: Optional[str]=None) -> dict
    record_audit(event: dict) -> None
    set_thresholds(...) to override at runtime (optional)
Configurable via environment variables.

Security notes:
- Do NOT include raw device ids, plaintext, or keys in audit logs; only include hashed/opaque identifiers.
- Protect audit log storage access with strong ACLs (outside the scope of this module).
"""

from typing import Optional, Dict, Any
import os
import time
import logging
import threading
import hashlib
import json
from collections import defaultdict

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Environment-configurable thresholds (defaults tuned conservatively)
THRESH_ALLOW = int(os.environ.get("POLICY_ALLOW_THRESHOLD", "70"))        # >= -> allow
THRESH_REAUTH = int(os.environ.get("POLICY_REAUTH_THRESHOLD", "40"))      # >= and < allow -> require reauth
# < THRESH_REAUTH -> block

# Canary / shadow controls
SHADOW_MODE = os.environ.get("POLICY_SHADOW_MODE", "false").lower() in ("1", "true", "yes")
CANARY_FRACTION = float(os.environ.get("POLICY_CANARY_FRACTION", "1.0"))  # 0..1.0, 1.0 = full enforcement

# Limit exception (approval) rate per token / per user window
EXCEPTION_QUOTA = int(os.environ.get("POLICY_EXCEPTION_QUOTA", "5"))      # exceptions per 24h per token/user
EXCEPTION_WINDOW_SEC = int(os.environ.get("POLICY_EXCEPTION_WINDOW_SEC", str(24 * 3600)))

# Audit log file (ensure access control in production)
AUDIT_LOG_PATH = os.environ.get("POLICY_AUDIT_LOG_PATH", "/var/log/secure_messaging_policy_audit.log")
# In dev, fallback to local file
if AUDIT_LOG_PATH == "":
    AUDIT_LOG_PATH = "/tmp/policy_audit.log"

# internal in-memory store for exception quotas (simple sliding window)
_exception_events = defaultdict(list)  # key -> list[timestamps]
_exception_lock = threading.Lock()

# Secure hashing helper for identifiers (so we don't log raw ids)
def _opaque_id(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    try:
        h = hashlib.sha256(val.encode("utf-8")).hexdigest()
        return h
    except Exception:
        return None

# Write audit event (append JSON line). Best-effort - in production use structured audit system.
def record_audit(event: Dict[str, Any]) -> None:
    """
    Write an audit event as a JSON line.
    `event` should contain only non-sensitive fields; this function will add timestamp and sanitize.
    """
    safe_event = dict(event)  # shallow copy
    safe_event.setdefault("ts", int(time.time()))
    # Ensure only allowed keys (enforce a whitelist)
    allowed_keys = {
        "ts", "token_hash", "action", "risk", "policy", "reason", "client_ip_hash",
        "metadata_summary", "actor", "admin_action", "note"
    }
    safe_event = {k: v for k, v in safe_event.items() if k in allowed_keys}
    try:
        # Append JSON line
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe_event, separators=(",", ":"), ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write audit event")

def _within_exception_quota(key: str) -> bool:
    """Check+update exception quota for `key` (opaque id)."""
    now = time.time()
    window_start = now - EXCEPTION_WINDOW_SEC
    with _exception_lock:
        events = _exception_events.get(key, [])
        # purge old
        events = [ts for ts in events if ts >= window_start]
        if len(events) >= EXCEPTION_QUOTA:
            # update back and return False
            _exception_events[key] = events
            return False
        events.append(now)
        _exception_events[key] = events
        return True

def _should_enforce_canary(token: str) -> bool:
    """
    Decide if this token should be subject to enforcement based on CANARY_FRACTION.
    Deterministic by hashing token so that repeated requests for same token are consistent.
    """
    try:
        if CANARY_FRACTION >= 1.0:
            return True
        if CANARY_FRACTION <= 0.0:
            return False
        h = hashlib.sha256(token.encode("utf-8")).digest()
        # Use first 8 bytes as int
        val = int.from_bytes(h[:8], "big") / float(2**64)
        return val < CANARY_FRACTION
    except Exception:
        # if anything wrong, be conservative: enforce
        return True

def decide_action(
    risk_score: int,
    token: str,
    metadata_summary: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
    actor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decide policy action given risk_score (0..100 with higher = safer).
    Returns dict:
        { "action": "allow"|"require_reauth"|"block"|"pending_approval",
          "policy": same as action,
          "enforced": bool (False in shadow mode or canary not enforced),
          "reason": "human readable reason",
          "token_hash": "<sha256>",
        }

    Side effects:
    - Writes an audit record via record_audit()
    """
    # sanitize inputs
    token_hash = _opaque_id(token)
    client_ip_hash = _opaque_id(client_ip)
    metadata_summary = metadata_summary or {}

    # compute raw decision from thresholds
    if risk_score >= THRESH_ALLOW:
        raw_action = "allow"
        reason = "risk >= allow_threshold"
    elif risk_score >= THRESH_REAUTH:
        raw_action = "require_reauth"
        reason = "risk in reauth range"
    else:
        raw_action = "block"
        reason = "risk < reauth_threshold (suspicious)"

    # apply exception/pending approval logic: if metadata indicates exception_flag, consider pending_approval
    if metadata_summary.get("exception_flag"):
        # check quota for actor or token; choose actor if present else token_hash
        quota_key = actor or token
        if _within_exception_quota(quota_key):
            # allow with special handling: mark as pending_approval if risk low, otherwise allow with stricter TTL
            if raw_action == "block":
                raw_action = "pending_approval"
                reason = "exception requested by user; queued for admin review"
            else:
                # allow but mark that exception used
                reason = "exception used; allowed but logged"
        else:
            raw_action = "block"
            reason = "exception quota exceeded; blocked"

    # determine enforcement based on shadow and canary
    enforce = True
    if SHADOW_MODE:
        enforce = False
    else:
        if not _should_enforce_canary(token):
            # in canary fraction < 1, don't enforce for this token
            enforce = False

    # map raw_action to policy and final action
    policy = raw_action
    if not enforce:
        # when not enforcing, we still return a 'simulated' policy but enforced=False
        action = "allow"  # safe fallback: allow in non-enforced mode
    else:
        # enforce raw action directly
        action = raw_action

    event = {
        "token_hash": token_hash,
        "action": action,
        "policy": policy,
        "risk": int(risk_score),
        "reason": reason,
        "client_ip_hash": client_ip_hash,
        "metadata_summary": {
            # include non-identifying summary elements only
            "padded_size": metadata_summary.get("padded_size"),
            "dest_count": metadata_summary.get("dest_count"),
            "exception_flag": bool(metadata_summary.get("exception_flag", False)),
        },
        "actor": _opaque_id(actor) if actor else None,
    }

    # record audit (best-effort)
    try:
        record_audit(event)
    except Exception:
        logger.exception("Failed to record audit event")

    return {
        "action": action,
        "policy": policy,
        "enforced": enforce,
        "reason": reason,
        "token_hash": token_hash,
    }

# Optional helper to update thresholds at runtime (useful for ops/admin)
_threshold_lock = threading.Lock()
def set_thresholds(allow: Optional[int] = None, reauth: Optional[int] = None) -> None:
    global THRESH_ALLOW, THRESH_REAUTH
    with _threshold_lock:
        if allow is not None:
            THRESH_ALLOW = int(allow)
        if reauth is not None:
            THRESH_REAUTH = int(reauth)
    logger.info("Policy thresholds updated: allow=%s reauth=%s", THRESH_ALLOW, THRESH_REAUTH)

# Expose small runtime status
def status() -> Dict[str, Any]:
    return {
        "allow_threshold": THRESH_ALLOW,
        "reauth_threshold": THRESH_REAUTH,
        "shadow_mode": SHADOW_MODE,
        "canary_fraction": CANARY_FRACTION,
        "exception_quota": EXCEPTION_QUOTA,
    }
