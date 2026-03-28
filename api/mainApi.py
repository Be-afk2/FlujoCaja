from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routers import auth, gastos, tipos,subtipos

app = FastAPI()

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

app.include_router(gastos.router)
app.include_router(auth.router)
app.include_router(tipos.router)
app.include_router(subtipos.router)

##uvicorn api.mainApi:app --reload