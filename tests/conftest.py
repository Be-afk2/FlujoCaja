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


@pytest.fixture()
def crear_entidad(client):
    def _crear(
        headers: dict,
        nombre: str = "Entidad test",
        tipo: str = "persona",
        descripcion: str | None = None,
    ) -> dict:
        body: dict = {"nombre": nombre, "tipo": tipo}
        if descripcion is not None:
            body["descripcion"] = descripcion
        r = client.post("/entidades/", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _crear


@pytest.fixture()
def obtener_moneda(client):
    def _obtener(headers: dict, indice: int = 0) -> int:
        monedas = client.get("/monedas/", headers=headers).json()
        assert len(monedas) > indice
        return monedas[indice]["id"]

    return _obtener


@pytest.fixture()
def crear_deuda(client, obtener_moneda):
    def _crear(
        headers: dict,
        entidad_id: int,
        monto: float = 1000.0,
        direccion: str = "cobrar",
        moneda_id: int | None = None,
        cuenta_inicial_id: int | None = None,
        descripcion: str | None = None,
        fecha: str | None = None,
        vencimiento: str | None = None,
    ) -> dict:
        if moneda_id is None:
            moneda_id = obtener_moneda(headers)
        body: dict = {
            "entidad_id": entidad_id,
            "direccion": direccion,
            "monto_original": monto,
            "moneda_id": moneda_id,
        }
        if cuenta_inicial_id is not None:
            body["cuenta_inicial_id"] = cuenta_inicial_id
        if descripcion is not None:
            body["descripcion"] = descripcion
        if fecha is not None:
            body["fecha"] = fecha
        if vencimiento is not None:
            body["vencimiento"] = vencimiento
        r = client.post("/deudas/", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _crear


@pytest.fixture()
def crear_pago(client):
    def _crear(
        headers: dict,
        deuda_id: int,
        cuenta_id: int,
        monto: float,
        fecha: str | None = None,
        descripcion: str | None = None,
    ) -> dict:
        body: dict = {"monto": monto, "cuenta_id": cuenta_id}
        if fecha is not None:
            body["fecha"] = fecha
        if descripcion is not None:
            body["descripcion"] = descripcion
        r = client.post(f"/deudas/{deuda_id}/pagos", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _crear
