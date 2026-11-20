from sqlalchemy import event

from bd.database import engine


def test_crear_usuario(client, registrar_usuario):
    usuario = registrar_usuario("ana")
    assert "id" in usuario
    assert usuario["name"] == "ana"
    assert "passw" not in usuario
    assert "apellido" not in usuario


def test_login_ok(client, registrar_usuario, login):
    registrar_usuario("bruno")
    data = login("bruno")
    assert "token" in data
    assert data["user"]["name"] == "bruno"


def test_login_credenciales_invalidas(client, registrar_usuario):
    registrar_usuario("carla")
    r = client.post("/auth/login", json={"name": "carla", "passw": "incorrecta", "recordar": False})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_sesion_actual(client, auth_headers):
    headers = auth_headers("diego")
    r = client.get("/auth", headers=headers)
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "diego"


def test_logout(client, auth_headers):
    headers = auth_headers("elena")
    r = client.delete("/auth", headers=headers)
    assert r.status_code == 200

    r = client.get("/auth", headers=headers)
    assert r.status_code == 401


def test_perfil_me(client, auth_headers):
    headers = auth_headers("fausto", passw="clave123")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "fausto"
    assert data["apellido"] == "Apellido"


def test_perfil_me_sin_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_actualizar_perfil(client, auth_headers):
    headers = auth_headers("gustavo")
    r = client.put("/auth/me", json={"name": "Gus", "apellido": "Nuevo"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Gus"
    assert r.json()["apellido"] == "Nuevo"

    r = client.get("/auth/me", headers=headers)
    assert r.json()["name"] == "Gus"


def test_actualizar_perfil_sin_campos(client, auth_headers):
    headers = auth_headers("hector")
    r = client.put("/auth/me", json={}, headers=headers)
    assert r.status_code == 400


def test_cambiar_password_ok(client, auth_headers, login):
    headers = auth_headers("ines")
    r = client.put(
        "/auth/me/password",
        json={"passw_actual": "clave123", "passw_nueva": "nueva456"},
        headers=headers,
    )
    assert r.status_code == 200

    data = login("ines", "nueva456")
    assert "token" in data


def _contar_selects_auth(consulta: str) -> bool:
    normalizada = consulta.upper()
    return "FROM SESION" in normalizada or "FROM USER" in normalizada


def test_cache_auth_evita_consultas_repetidas(client, auth_headers):
    headers = auth_headers("cache")
    consultas = []

    def contar(conn, cursor, statement, parameters, context, executemany):
        if _contar_selects_auth(statement):
            consultas.append(statement)

    event.listen(engine, "before_cursor_execute", contar)
    try:
        assert client.get("/auth/me", headers=headers).status_code == 200
        primera = len(consultas)
        consultas.clear()

        assert client.get("/auth/me", headers=headers).status_code == 200
        segunda = len(consultas)
    finally:
        event.remove(engine, "before_cursor_execute", contar)

    assert primera >= 1, "la primera peticion debe leer sesion y usuario"
    assert segunda == 0, "la segunda peticion debe resolverse desde el cache"


def test_logout_invalida_el_cache(client, auth_headers):
    headers = auth_headers("cache_logout")
    assert client.get("/movimientos/", headers=headers).status_code == 200

    assert client.delete("/auth", headers=headers).status_code == 200

    r = client.get("/movimientos/", headers=headers)
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_nuevo_login_invalida_el_token_anterior(
    client, registrar_usuario, login
):
    registrar_usuario("rotacion")
    primero = login("rotacion")
    headers_viejo = {"Authorization": f"Bearer {primero['token']}"}
    assert client.get("/auth/me", headers=headers_viejo).status_code == 200

    segundo = login("rotacion")

    assert client.get("/auth/me", headers=headers_viejo).status_code == 401
    headers_nuevo = {"Authorization": f"Bearer {segundo['token']}"}
    assert client.get("/auth/me", headers=headers_nuevo).status_code == 200
