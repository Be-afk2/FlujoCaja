import uuid
from pydantic import BaseModel, Field
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

class MeResponse(SQLModel):
    id: uuid.UUID
    name: str
    apellido: str

class UserProfileUpdate(BaseModel):
    name: str | None = None
    apellido: str | None = None

class PasswordChange(BaseModel):
    passw_actual: str
    passw_nueva: str = Field(min_length=4)