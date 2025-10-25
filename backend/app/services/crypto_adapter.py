# backend/app/services/crypto_adapter.py
"""
Crypto adapter service for server public key management.
"""

import logging
from typing import Dict, Any, Optional
from app.services import key_manager as km_module

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def get_server_public_keys() -> Dict[str, Any]:
    """
    Get server public keys for hybrid key exchange.
    Returns server X25519 and PQC public keys.
    """
    try:
        if km_module.km is None:
            return {
                "error": "KeyManager not available",
                "x25519_pub_b64": None,
                "pqc_pub_b64": None,
                "pqc_enabled": False
            }
        
        return km_module.km.export_public_keys()
    except Exception as e:
        logger.exception("Failed to get server public keys: %s", str(e))
        return {
            "error": str(e),
            "x25519_pub_b64": None,
            "pqc_pub_b64": None,
            "pqc_enabled": False
        }
