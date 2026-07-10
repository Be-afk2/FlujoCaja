from pydantic import BaseModel
from typing import Optional


class CuentaDTO(BaseModel):
    nombre: str
    descripcion: str
    tipo: int
    moneda: int


class SubCuentaDTO(BaseModel):
    nombre: str
    descripcion: str


class CuentaResponse(BaseModel):
    id: int
    nombre: str
    saldo: float
    descripcion: Optional[str]
    tipo_id: int
    moneda_id: int
