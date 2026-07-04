from fastapi import APIRouter

router = APIRouter(prefix="/movimientos")

@router.get("/")
def listar_movimientos():
    return "hola"
