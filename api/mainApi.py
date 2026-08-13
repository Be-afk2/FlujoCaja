import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.dependencies import validate_token
from api.routers import auth, cuenta, datos, moneda, movimientos, resumen, subtipos, tipos
from bd.logging import setup_logging
from config import DATABASE_PATH, WEB_DIR, is_debug_enabled

# ==================== CONFIGURACIÓN DE LOGGING ====================
DEBUG_MODE = is_debug_enabled()
setup_logging(debug=DEBUG_MODE)
logger = logging.getLogger(__name__)
if DEBUG_MODE:
    logger.debug("🔍 Modo DEBUG activado - Logging detallado habilitado")

app = FastAPI(
    title="FlujoCaja API",
    description="API local para gestión de flujo de caja personal",
    version="0.4.0",
)

# CORS abierto para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requests en modo DEBUG
if DEBUG_MODE:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f"→ Incoming request: {request.method} {request.url.path}")
        logger.debug(f"  Headers: {dict(request.headers)}")
        
        response = await call_next(request)
        
        logger.debug(f"← Response status: {response.status_code} for {request.method} {request.url.path}")
        return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if DEBUG_MODE:
        logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail} on {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "path": str(request.url)
        },
        headers=exc.headers,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if DEBUG_MODE:
        logger.error(f"Validation Error: {errors} on {request.url.path}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Error de validación",
            "status": 422,
            "path": str(request.url),
            "details": errors
        }
    )

# Servir frontend estático
if WEB_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

# Health checks
@app.get("/health")
def health():
    return {"message": "alive", "version": app.version, "database": str(DATABASE_PATH)}

@app.get("/health/token")
def health_token(_=Depends(validate_token)):
    return {"message": "Token válido", "status": "true"}

app.include_router(movimientos.router, dependencies=[Depends(validate_token)])
app.include_router(auth.router)
app.include_router(tipos.router, dependencies=[Depends(validate_token)])
app.include_router(subtipos.router, dependencies=[Depends(validate_token)])
app.include_router(cuenta.router, dependencies=[Depends(validate_token)])
app.include_router(moneda.router, dependencies=[Depends(validate_token)])
app.include_router(resumen.router, dependencies=[Depends(validate_token)])
app.include_router(datos.router, dependencies=[Depends(validate_token)])

