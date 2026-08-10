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

    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "back3"
