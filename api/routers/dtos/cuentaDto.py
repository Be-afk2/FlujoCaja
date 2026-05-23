import uuid
from pydantic import BaseModel
from sqlmodel import SQLModel

class CuentaDTO(BaseModel):
    nombre:str
    descripcion:str
    tipo:str

class SubCuentaDTO(BaseModel):
    nombre:str
    descripcion:str

class CuentaDTO(BaseModel):
    nombre: str
    descripcion: str
    tipo: int
    moneda:int
