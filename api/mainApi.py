from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routers import auth, cuenta, gastos, moneda, tipos,subtipos
from api.dependencies import validate_token

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "path": str(request.url)
        }
    )

app.include_router(gastos.router, dependencies=[Depends(validate_token)])
app.include_router(auth.router)
app.include_router(tipos.router, dependencies=[Depends(validate_token)])
app.include_router(subtipos.router, dependencies=[Depends(validate_token)])
app.include_router(cuenta.router, dependencies=[Depends(validate_token)])
app.include_router(moneda.router, dependencies=[Depends(validate_token)])

