from fastapi import APIRouter
router = APIRouter()
router = APIRouter(prefix="/gastos")
@router.get("/")
def get_test():
    return "hola"
 