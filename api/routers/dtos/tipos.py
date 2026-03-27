
from pydantic import BaseModel
from sqlmodel import SQLModel
from typing import List, Optional

class TipoCreateDto(BaseModel):
    nombre: str
    descripcion: str

class OneId(BaseModel):
    id:int

class SubtipoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]


class SubTipoCreate(BaseModel):
    nombre: str
    descripcion : str
    tipo : int

class TipoResponse(BaseModel):
    tipo: int
    nombre: str
    subtipos: List[SubtipoResponse]