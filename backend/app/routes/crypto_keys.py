# backend/app/routes/crypto_keys.py
from fastapi import APIRouter, HTTPException
from app.services import key_manager as km_module

router = APIRouter()

@router.get("/crypto/keys")
def get_server_keys():
    """
    Return the server public keys for performing a hybrid key exchange.
    Clients call this to receive server X25519 public key and (if enabled) PQC public key.
    """
    try:
        if km_module.km is None:
            raise HTTPException(status_code=503, detail="KeyManager not available")
        
        return km_module.km.export_public_keys()
    except Exception as e:
        raise HTTPException(status_code=500, detail="failed to retrieve server keys")
