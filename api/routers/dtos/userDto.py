from pydantic import BaseModel

class UserDTO(BaseModel):
    name: str
    apellido:str
    passw: str
class UserLogin(BaseModel):
    name : str
    passw: str