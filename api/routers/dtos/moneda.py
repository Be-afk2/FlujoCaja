from pydantic import BaseModel
from sqlmodel import SQLModel

class MonedaDTO(BaseModel):
    nombre: str
    simbolo: str