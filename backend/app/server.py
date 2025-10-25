# backend/app/server.py
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("secure_messaging_backend")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# Environment flags
DEMO_KEYS = os.environ.get("DEMO_KEYS", "false").lower() in ("1", "true", "yes")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app = FastAPI(
    title="Secure Messaging Backend",
    description="Backend for encrypted ephemeral messaging (storage, keys, ML, policy).",
    version="0.1.0",
)

# CORS - adjust origins for production strictly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount routers (import inside try blocks so missing modules are optional) ---
# crypto router (keys endpoint)
try:
    from app.routes import crypto as crypto_router
    app.include_router(crypto_router.router, prefix="", tags=["crypto"])
    logger.info("Mounted routes.crypto")
except Exception:
    logger.exception("Failed to mount routes.crypto (it may be missing).")

# crypto_keys (if you have a separate module)
try:
    from app.routes import crypto_keys as crypto_keys_router
    app.include_router(crypto_keys_router.router, prefix="", tags=["crypto_keys"])
    logger.info("Mounted routes.crypto_keys")
except Exception:
    logger.info("routes.crypto_keys not present; skipping.")

# ML (observe / admin / score)
try:
    from app.routes import ml as ml_router
    app.include_router(ml_router.router, prefix="", tags=["ml"])
    logger.info("Mounted routes.ml")
except Exception:
    logger.info("routes.ml not present; skipping.")

try:
    from app.routes import ml_score as ml_score_router
    app.include_router(ml_score_router.router, prefix="", tags=["ml_score"])
    logger.info("Mounted routes.ml_score")
except Exception:
    logger.info("routes.ml_score not present; skipping.")

# send / fetch / read / admin_ml routers
for modname in ("send", "fetch", "read", "admin_ml"):
    try:
        module = __import__(f"app.routes.{modname}", fromlist=["router"])
        router = getattr(module, "router", None)
        if router is not None:
            app.include_router(router, prefix="", tags=[modname])
            logger.info("Mounted routes.%s", modname)
    except Exception:
        logger.info("routes.%s not present; skipping.", modname)

# demo key route -- only enable when DEMO_KEYS True
if DEMO_KEYS:
    try:
        from app.routes import key as key_router
        app.include_router(key_router.router, prefix="", tags=["key"])
        logger.info("Mounted demo route: routes.key (DEMO_KEYS enabled)")
    except Exception:
        logger.info("routes.key not present or failed; skipping demo key route.")

# Generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception processing request: %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Health & readiness endpoints
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": app.version}

@app.get("/ready", tags=["health"])
async def ready():
    ready_info = {"ready": True}
    try:
        from app.services import ml_adapter
        ml = getattr(ml_adapter, "ml", None)
        if ml is None:
            ready_info["ml"] = "unavailable"
        else:
            try:
                ready_info["ml"] = ml.health()
            except Exception:
                ready_info["ml"] = "error"
    except Exception:
        ready_info["ml"] = "not_installed"
    return ready_info

# Startup event
@app.on_event("startup")
async def on_startup():
    logger.info("Starting Secure Messaging Backend...")
    try:
        from app.services import ml_adapter
        ml = getattr(ml_adapter, "ml", None)
        if ml is not None:
            logger.info("ML adapter present; model health: %s", getattr(ml, "health", lambda: {})())
    except Exception:
        logger.info("ML adapter not present at startup.")

# Shutdown event
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down Secure Messaging Backend...")

# Root path
@app.get("/", tags=["root"])
async def root():
    return {"service": "secure_messaging_backend", "version": app.version}
