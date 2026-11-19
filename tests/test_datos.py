import sqlite3

from bd.database import engine
from config import DATABASE_PATH


def test_conexiones_sqlite_tienen_pragmas_y_timeout():
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert connection.exec_driver_sql("PRAGMA synchronous").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() == 5000


def test_backup_requiere_token(client):
    r = client.get("/datos/backup")
    assert r.status_code == 401


def test_backup_descarga_archivo(client, auth_headers):
    headers = auth_headers("back1")
    r = client.get("/datos/backup", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/octet-stream")
    assert r.content.startswith(b"SQLite format 3")


def test_restaurar_requiere_token(client):
    r = client.post("/datos/restaurar", files={"file": ("x.db", b"datos", "application/octet-stream")})
    assert r.status_code == 401


def test_restaurar_archivo_invalido(client, auth_headers):
    headers = auth_headers("back2")
    r = client.post(
        "/datos/restaurar",
        files={"file": ("falso.db", b"no soy sqlite", "application/octet-stream")},
        headers=headers,
    )
    assert r.status_code == 400


def test_restaurar_backup_valido(client, auth_headers, registrar_usuario):
    headers = auth_headers("back3")
    registrar_usuario("extra")

    r = client.get("/datos/backup", headers=headers)
    assert r.status_code == 200

    r = client.post(
        "/datos/restaurar",
        files={"file": ("backup.db", r.content, "application/octet-stream")},
        headers=headers,
    )
    assert r.status_code == 200

    with sqlite3.connect(str(DATABASE_PATH)) as con:
        assert con.execute("PRAGMA integrity_check").fetchone() == ("ok",)

    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "back3"
