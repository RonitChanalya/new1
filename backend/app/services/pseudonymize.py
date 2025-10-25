# backend/app/services/pseudonymize.py
"""
Pseudonymization service for safe logging and data handling.
"""

import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def pseudonymize_token(token: str) -> str:
    """
    Create a pseudonym for a token for safe logging.
    Returns a deterministic but opaque identifier.
    """
    if not token:
        return "null"
    
    try:
        # Create deterministic hash
        hash_input = f"token:{token}:pseudonym"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    except Exception as e:
        logger.exception("Failed to pseudonymize token: %s", str(e))
        return "error"


def pseudonymize_user_id(user_id: str) -> str:
    """
    Create a pseudonym for a user ID for safe logging.
    """
    if not user_id:
        return "null"
    
    try:
        hash_input = f"user:{user_id}:pseudonym"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    except Exception as e:
        logger.exception("Failed to pseudonymize user ID: %s", str(e))
        return "error"


def pseudonymize_ip(ip_address: str) -> str:
    """
    Create a pseudonym for an IP address for safe logging.
    """
    if not ip_address:
        return "null"
    
    try:
        hash_input = f"ip:{ip_address}:pseudonym"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    except Exception as e:
        logger.exception("Failed to pseudonymize IP: %s", str(e))
        return "error"
