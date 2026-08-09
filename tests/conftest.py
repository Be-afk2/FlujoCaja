import os
import tempfile

os.environ["APPDATA"] = tempfile.mkdtemp(prefix="flujocaja_test_")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from api.mainApi import app
from bd.database import engine
from bd.seeds import seed_db
from config import DATA_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def reset_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    seed_db()
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def registrar_usuario(client):
    def _registrar(name: str, apellido: str = "Apellido", passw: str = "clave123") -> dict:
        r = client.post("/auth/register", json={"name": name, "apellido": apellido, "passw": passw})
        assert r.status_code == 201, r.text
        return r.json()

    return _registrar


@pytest.fixture()
def login(client):
    def _login(name: str, passw: str = "clave123") -> dict:
        r = client.post("/auth/login", json={"name": name, "passw": passw, "recordar": False})
        assert r.status_code == 200, r.text
        return r.json()

    return _login


@pytest.fixture()
def auth_headers(registrar_usuario, login):
    def _headers(name: str, passw: str = "clave123") -> dict:
        registrar_usuario(name, passw=passw)
        data = login(name, passw)
        return {"Authorization": f"Bearer {data['token']}"}

    return _headers


@pytest.fixture()
def obtener_ids_catalogos(client):
    def _ids(headers: dict) -> tuple[int, int]:
        tipocuentas = client.get("/cuentas/tipos-cuenta", headers=headers).json()
        monedas = client.get("/monedas/", headers=headers).json()
        assert tipocuentas and monedas
        return tipocuentas[0]["id"], monedas[0]["id"]

    return _ids


@pytest.fixture()
def crear_tipo(client):
    def _crear(headers: dict, nombre: str = "Tipo test", descripcion: str | None = None) -> dict:
        r = client.post("/tipos/", json={"nombre": nombre, "descripcion": descripcion}, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _crear


@pytest.fixture()
def crear_cuenta(client, obtener_ids_catalogos):
    def _crear(headers: dict, nombre: str = "Cuenta test", tipo: int | None = None, moneda: int | None = None) -> dict:
        tipo_id, moneda_id = obtener_ids_catalogos(headers)
        r = client.post(
            "/cuentas/",
            json={
                "nombre": nombre,
                "descripcion": "",
                "tipo": tipo if tipo is not None else tipo_id,
                "moneda": moneda if moneda is not None else moneda_id,
            },
            headers=headers,
        )
        assert r.status_code == 201, r.text
        return r.json()

    return _crear


@pytest.fixture()
def crear_movimiento(client, crear_tipo):
    def _crear(
        headers: dict,
        cuenta_id: int,
        monto: float,
        tipo_id: int | None = None,
        descripcion: str | None = None,
        fecha: str | None = None,
    ) -> dict:
        if tipo_id is None:
            tipo_id = crear_tipo(headers)["id"]
        body = {"monto": monto, "tipo_id": tipo_id, "cuenta_id": cuenta_id}
        if descripcion is not None:
            body["descripcion"] = descripcion
        if fecha is not None:
            body["fecha"] = fecha
        r = client.post("/movimientos/", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _crear
