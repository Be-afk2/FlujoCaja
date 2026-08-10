import logging
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from bd.database import engine
from bd.models.user import User
from config import DATABASE_PATH
from api.dependencies import validate_token

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
        src = sqlite3.connect(str(DATABASE_PATH))
        try:
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

    try:
        # Descartar conexiones abiertas antes de reemplazar el archivo
        engine.dispose()
        with open(DATABASE_PATH, "wb") as f:
            f.write(contenido)

        # Verificar que la BD restaurada sea legible
        con = sqlite3.connect(str(DATABASE_PATH))
        con.execute("PRAGMA integrity_check")
        con.close()
    except Exception as e:
        logger.error("Error al restaurar base de datos: %s", e)
        raise HTTPException(status_code=400, detail="No se pudo restaurar la base de datos")

    return {"message": "Base de datos restaurada correctamente"}


def _eliminar_archivo(path: str) -> None:
    """Elimina el archivo temporal cuando la respuesta termina de enviarse."""
    Path(path).unlink(missing_ok=True)
