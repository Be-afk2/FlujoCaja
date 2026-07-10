from fastapi import APIRouter, Depends, HTTPException
from typing import List

from bd.crud.movimiento import (
    crear_movimiento,
    get_movimiento,
    update_movimiento,
    delete_movimiento,
    movimientos_filtrados,
)
from bd.models.user import User
from api.dependencies import validate_token
from .dtos.movimientoDto import MovimientoCreate, MovimientoUpdate, MovimientoFilter, MovimientoResponse, MovimientoListResponse

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.get("/", response_model=MovimientoListResponse, summary="Listar movimientos con filtros y paginación")
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


@router.post("/", status_code=201, response_model=MovimientoResponse, summary="Crear un nuevo movimiento")
def crear(datos: MovimientoCreate, user: User = Depends(validate_token)):
    try:
        mov = crear_movimiento(
            monto=datos.monto,
            tipo_id=datos.tipo_id,
            cuenta_id=datos.cuenta_id,
            user=user,
            subtipo_id=datos.subtipo_id,
            descripcion=datos.descripcion,
            fecha=datos.fecha,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return mov


@router.get("/{movimiento_id}", response_model=MovimientoResponse, summary="Obtener movimiento por ID")
def obtener(movimiento_id: int, user: User = Depends(validate_token)):
    mov = get_movimiento(movimiento_id, user)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return mov


@router.put("/{movimiento_id}", response_model=MovimientoResponse, summary="Actualizar un movimiento existente")
def actualizar(movimiento_id: int, datos: MovimientoUpdate, user: User = Depends(validate_token)):
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return mov


@router.delete("/{movimiento_id}", summary="Eliminar un movimiento")
def eliminar(movimiento_id: int, user: User = Depends(validate_token)):
    ok = delete_movimiento(movimiento_id, user)
    if not ok:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return {"message": "Movimiento eliminado"}
