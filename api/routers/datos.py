import logging
import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from api.dependencies import validate_token
from bd.database import engine
from bd.models.user import User
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datos", tags=["Datos"])

BACKUP_FILENAME = "flujocaja_backup.db"
SQLITE_HEADER = b"SQLite format 3\x00"


@router.get("/backup", summary="Descargar copia de seguridad de la base de datos")
def backup_db(user: User = Depends(validate_token)):
    if not DATABASE_PATH.exists():
        raise HTTPException(status_code=404, detail="No se encontró la base de datos")

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    try:
        # Copia consistente usando la API de backup de SQLite (no copiar en caliente)
        src = sqlite3.connect(str(DATABASE_PATH), timeout=5)
        try:
            checkpoint = src.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if checkpoint and checkpoint[0]:
                logger.warning(
                    "WAL checkpoint ocupado; la API de backup hará la copia consistente"
                )
            dst = sqlite3.connect(tmp.name)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
    except Exception as e:
        Path(tmp.name).unlink(missing_ok=True)
        logger.error("Error al generar backup: %s", e)
        raise HTTPException(status_code=500, detail="No se pudo generar el backup")

    return FileResponse(
        path=tmp.name,
        filename=BACKUP_FILENAME,
        media_type="application/octet-stream",
        background=BackgroundTask(_eliminar_archivo, tmp.name),
    )


@router.post("/restaurar", summary="Restaurar la base de datos desde un archivo")
async def restaurar_db(file: UploadFile, user: User = Depends(validate_token)):
    contenido = await file.read()

    if not contenido.startswith(SQLITE_HEADER):
        raise HTTPException(status_code=400, detail="El archivo no es una base de datos SQLite válida")

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        # Validar la copia antes de tocar la base activa y dejar el temporal en
        # el mismo volumen para que el reemplazo final sea atómico.
        with tempfile.NamedTemporaryFile(
            dir=DATABASE_PATH.parent, suffix=".restore", delete=False
        ) as tmp:
            tmp.write(contenido)
            tmp_path = Path(tmp.name)

        # sqlite3.connect() como context manager no cierra la conexion (solo
        # hace commit/rollback); en Windows el archivo queda bloqueado y el
        # unlink posterior falla con PermissionError.
        con = sqlite3.connect(str(tmp_path), timeout=5)
        try:
            resultado = con.execute("PRAGMA integrity_check").fetchone()
        finally:
            con.close()
        if not resultado or resultado[0] != "ok":
            raise HTTPException(
                status_code=400,
                detail="La base de datos restaurada no superó integrity_check",
            )

        # Cerrar conexiones del pool y retirar WAL/SHM antiguos para evitar que
        # SQLite los aplique por error al archivo recién restaurado.
        engine.dispose()
        Path(f"{DATABASE_PATH}-wal").unlink(missing_ok=True)
        Path(f"{DATABASE_PATH}-shm").unlink(missing_ok=True)
        os.replace(tmp_path, DATABASE_PATH)
        tmp_path = None
    except HTTPException:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        logger.error("Error al restaurar base de datos: %s", e)
        raise HTTPException(status_code=400, detail="No se pudo restaurar la base de datos")

    return {"message": "Base de datos restaurada correctamente"}


def _eliminar_archivo(path: str) -> None:
    """Elimina el archivo temporal cuando la respuesta termina de enviarse."""
    Path(path).unlink(missing_ok=True)
