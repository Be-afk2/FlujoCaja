import uuid
from pydantic import BaseModel
from sqlmodel import SQLModel

class UserDTO(BaseModel):
    name: str
    apellido:str
    passw: str
class UserLogin(BaseModel):
    name : str
    passw: str
    recordar: bool 

class UserPublic(SQLModel):
    id: uuid.UUID
    name: str

class UserWithToken(BaseModel):
    user: UserPublic
    token: str