# backend/app/deps.py
"""
Dependency providers for FastAPI routes.

These functions return singleton service instances from app.services.
They are intentionally thin so tests can override them with
`app.dependency_overrides[...] = my_mock`.

Notes:
- The ML adapter may be None if sklearn/joblib are not installed; callers
  should handle that case (returning 503 or falling back).
- The pseudonymize provider returns a callable `pseudonymize_token(str)->str`
  that routes can use for logging without importing the helper directly.
"""

from typing import Callable, Optional
from fastapi import Depends
from app.services import storage as _storage_module
from app.services import key_manager as _key_manager_module
from app.services import ml_adapter as _ml_adapter_module
from app.services import policy as _policy_module
try:
    from app.services import crypto_adapter as _crypto_adapter_module
except ImportError:
    _crypto_adapter_module = None

try:
    from app.services import pseudonymize as _pseudonymize_module
except ImportError:
    _pseudonymize_module = None


def get_storage() -> _storage_module.EphemeralStorage:
    """Return the global ephemeral storage instance (EphemeralStorage)."""
    return _storage_module.storage


def get_key_manager() -> _key_manager_module.KeyManager:
    """Return the global KeyManager singleton."""
    return _key_manager_module.km


def get_ml_adapter() -> Optional[object]:
    """
    Return the global ML adapter singleton (may be None if ML not available).
    Caller should check for None and handle gracefully.
    """
    return getattr(_ml_adapter_module, "ml", None)


def get_policy_engine() -> object:
    """Return the policy module (provides decide_action, record_audit, etc.)."""
    return _policy_module


def get_crypto_adapter() -> object:
    """Return the crypto adapter module (crypto utilities)."""
    return _crypto_adapter_module


def get_pseudonymizer() -> Callable[[str], str]:
    """
    Return a callable pseudonymize_token(token: str) -> str for safe logging.
    This lets routes use dependency injection for testing/mocking.
    """
    if _pseudonymize_module is None:
        # Fallback implementation
        def fallback_pseudonymize(token: str) -> str:
            import hashlib
            if not token:
                return "null"
            return hashlib.sha256(token.encode()).hexdigest()[:12]
        return fallback_pseudonymize
    return _pseudonymize_module.pseudonymize_token
