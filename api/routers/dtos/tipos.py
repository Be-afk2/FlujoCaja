
from pydantic import BaseModel
from sqlmodel import SQLModel
from typing import Optional

class TipoCreateDto(BaseModel):
    nombre: str
    descripcion: str

class OneId(BaseModel):
    id:str