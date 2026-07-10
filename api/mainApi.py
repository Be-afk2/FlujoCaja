import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routers import auth, cuenta, moneda, movimientos, resumen, tipos, subtipos
from api.dependencies import validate_token
from bd.crud.sesion import obtener_usuario_por_token
from config import is_debug_enabled, API_HOST, API_PORT

# ==================== CONFIGURACIÓN DE LOGGING ====================
DEBUG_MODE = is_debug_enabled()

if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.debug("🔍 Modo DEBUG activado - Logging detallado habilitado")
else:
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)

app = FastAPI(
    title="FlujoCaja API",
    description="API local para gestión de flujo de caja personal",
    version="0.3.0",
)

# Configuración de CORS — solo orígenes locales
origins = [f"http://{API_HOST}:{API_PORT}"]
if API_HOST == "127.0.0.1":
    origins.append("http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
        }
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

# Health checks
@app.get("/health")
def health():
    return {"message": "alive"}

@app.get("/health/token")
def health_token(token: str):
    usuario = obtener_usuario_por_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"})
    return {"message": "Token válido", "status": "true"}

app.include_router(movimientos.router, dependencies=[Depends(validate_token)])
app.include_router(auth.router)
app.include_router(tipos.router, dependencies=[Depends(validate_token)])
app.include_router(subtipos.router, dependencies=[Depends(validate_token)])
app.include_router(cuenta.router, dependencies=[Depends(validate_token)])
app.include_router(moneda.router, dependencies=[Depends(validate_token)])
app.include_router(resumen.router, dependencies=[Depends(validate_token)])

