from fastapi import APIRouter, Depends, HTTPException

from bd.crud.movimiento import (
    crear_movimiento,
    get_movimiento,
    update_movimiento,
    delete_movimiento,
    movimientos_filtrados,
)
from bd.models.user import User
from api.dependencies import validate_token
from .dtos.movimientoDto import MovimientoCreate, MovimientoUpdate, MovimientoFilter

router = APIRouter(prefix="/movimientos")


@router.get("/")
def listar_movimientos(filtros: MovimientoFilter = Depends(), user: User = Depends(validate_token)):
    resultados, total = movimientos_filtrados(
        user=user,
        pagina=filtros.pagina,
        cantidad=filtros.cantidad,
        fecha_desde=filtros.fecha_desde,
        fecha_hasta=filtros.fecha_hasta,
        cuenta_id=filtros.cuenta_id,
        tipo_id=filtros.tipo_id,
        subtipo_id=filtros.subtipo_id,
        es_ingreso=filtros.es_ingreso,
    )
    return {"data": resultados, "total": total, "pagina": filtros.pagina}


@router.post("/", status_code=201)
def crear(datos: MovimientoCreate, user: User = Depends(validate_token)):
    mov = crear_movimiento(
        monto=datos.monto,
        tipo_id=datos.tipo_id,
        cuenta_id=datos.cuenta_id,
        user=user,
        subtipo_id=datos.subtipo_id,
        descripcion=datos.descripcion,
        fecha=datos.fecha,
    )
    return mov


@router.get("/{movimiento_id}")
def obtener(movimiento_id: int, user: User = Depends(validate_token)):
    mov = get_movimiento(movimiento_id, user)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return mov


@router.put("/{movimiento_id}")
def actualizar(movimiento_id: int, datos: MovimientoUpdate, user: User = Depends(validate_token)):
    mov = update_movimiento(
        movimiento_id=movimiento_id,
        user=user,
        monto=datos.monto,
        tipo_id=datos.tipo_id,
        subtipo_id=datos.subtipo_id,
        cuenta_id=datos.cuenta_id,
        descripcion=datos.descripcion,
        fecha=datos.fecha,
    )
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return mov


@router.delete("/{movimiento_id}")
def eliminar(movimiento_id: int, user: User = Depends(validate_token)):
    ok = delete_movimiento(movimiento_id, user)
    if not ok:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return {"message": "Movimiento eliminado"}
