# backend/app/services/auth_helpers.py
import os
import hmac
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def _load_key_list(env_var: str) -> List[str]:
    """
    Read env var containing comma-separated api keys and return list.
    This lets ops rotate keys or provide multiple valid keys (e.g., for CI/admin).
    """
    raw = os.environ.get(env_var, "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return keys


def check_api_key(header_value: Optional[str], env_var: str) -> bool:
    """
    Constant-time comparison of the header value against one or more keys in env_var.
    Returns True if match; False otherwise.
    """
    if not header_value:
        return False

    valid_keys = _load_key_list(env_var)
    if not valid_keys:
        # no keys configured -> intentionally disable endpoint (fail closed)
        logger.error("No API keys configured for %s; endpoint should be disabled in production", env_var)
        return False

    hv = header_value.strip()
    for k in valid_keys:
        try:
            if hmac.compare_digest(hv, k):
                return True
        except Exception:
            # If compare_digest fails for unexpected reason, continue trying others
            continue
    return False
