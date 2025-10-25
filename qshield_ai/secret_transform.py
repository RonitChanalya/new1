# secret_transform.py
import os, hmac, hashlib
import numpy as np
from config import get
from typing import Sequence

def _get_hmac_key():
    return get("FEATURE_HMAC_KEY").encode()

def hash_token(token: str) -> str:
    key = _get_hmac_key()
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()

def seeded_random_projection(vector: Sequence[float], seed: str, out_dim: int = None):
    """
    Secret random projection: given input vector and secret seed, produce projected numeric vector.
    Deterministic for same seed. Helps prevent simple inversion if seed is secret.
    """
    vec = np.array(vector, dtype=float).reshape(-1)
    dim = vec.shape[0]
    if out_dim is None:
        out_dim = max(1, dim)
    # derive stable seed int
    seed_bytes = seed.encode()
    seed_int = int(hashlib.sha256(seed_bytes).hexdigest()[:16], 16) & 0xffffffff
    rng = np.random.RandomState(seed_int)
    # projection matrix
    P = rng.normal(loc=0.0, scale=1.0, size=(out_dim, dim))
    proj = P.dot(vec)
    # optional simple non-linear transform + clip
    proj = np.tanh(proj)  # keep values bounded [-1,1]
    return proj.tolist()

def transform_observation(token: str, vector: Sequence[float], out_dim: int = None):
    """
    Hash token for audit and use secret projection for features.
    Returns (token_hash, projected_vector)
    """
    token_hash = hash_token(token)
    seed = get("FEATURE_HMAC_KEY")
    proj = seeded_random_projection(vector, seed, out_dim=out_dim)
    return token_hash, proj
