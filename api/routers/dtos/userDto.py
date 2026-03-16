from pydantic import BaseModel

class UserDTO(BaseModel):
    name: str
    apellido:str
    passw: str