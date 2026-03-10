from fastapi import FastAPI
from routers import gastos, users

app = FastAPI()

app.include_router(gastos.router)
app.include_router(users.router)