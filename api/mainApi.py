import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routers import auth, cuenta, moneda, movimientos, tipos,subtipos
from api.dependencies import validate_token
from config import is_debug_enabled

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

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Permite todos los headers
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

app.include_router(movimientos.router, dependencies=[Depends(validate_token)])
app.include_router(auth.router)
app.include_router(tipos.router, dependencies=[Depends(validate_token)])
app.include_router(subtipos.router, dependencies=[Depends(validate_token)])
app.include_router(cuenta.router, dependencies=[Depends(validate_token)])
app.include_router(moneda.router, dependencies=[Depends(validate_token)])

