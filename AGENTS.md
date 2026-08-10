# FlujoCaja — AGENTS.md

## Entrypoints

- `main.py` — main app: starts DB → API (Uvicorn on `127.0.0.1:8000`) → PyQt6 WebEngine desktop window
- `app.py` — legacy CLI, still present under `menus/` and `widget/`

## Run commands

```powershell
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt     # dev only (pytest, httpx, ruff)
python main.py                  # full app (BD + API + web)
python main.py --api            # API only
python main.py --api --debug    # API with debug logging
python main.py --bd             # DB init only
python main.py --web            # web shell only
python -m pytest tests -v       # run tests (or .\run_tests.ps1)
python -m ruff check tests api/mainApi.py   # lint scoped (or .\run_lint.ps1)
```

## Architecture

- **Backend:** FastAPI (`api/mainApi.py`), routers in `api/routers/`
- **DB:** SQLite (`database.db`), SQLModel (`bd/models/`), CRUD in `bd/crud/`
- **Frontend:** static HTML/JS/Tailwind via CDN in `web/`, loaded by PyQt6 WebEngine
- **Auth:** simple SQLite token (single-session, no JWT). Bearer token via `Authorization` header. Validated against `sesion` table.
  - Unprotected routes: `/auth/*` (login, register, session check), `/health`
  - Protected routes (require `Depends(validate_token)`): `/movimientos`, `/tipos`, `/subtipos`, `/cuentas`, `/monedas`, `/resumen`, `/health/token`, `/auth/me`, `/datos`
- **Session:** Single session row in DB. Auth via `Authorization: Bearer <token>`, validated by `validate_token()` in `api/dependencies.py` which resolves the `User`. Legacy `obtener_sesion()` still present but deprecated.
- `database.db` is gitignored; auto-created on first run.

## Key refactors (Fase 4 — API mantenible)

- Routes renamed: `/cuenta` → `/cuentas`, `/moneda` → `/monedas`, `/auth/create` → `/auth/register`, `/auth/life/*` → `/health/*`
- DTOs introduced: `CuentaResponse`, `MonedaResponse`, `MovimientoListResponse`, `TipoListResponse`, `TipoDetailResponse`; `response_model` on every endpoint
- `RequestValidationError` handler normalizes 422 to `{"error", "status", "path", "details"}`
- Auth errors return 401 with `WWW-Authenticate` header
- CORS restricted to `["http://127.0.0.1:8000", "http://localhost:8000"]`
- `FastAPI(title=..., description=..., version="0.3.0")` with `tags` on all 7 routers
- All POST creation endpoints have `status_code=201`

## Key refactors (Fase 8 — Perfil, contraseña, backup/restaurar)

- `/auth/me` GET returns current user (DTO `MeResponse`); PUT updates `name`/`apellido` (`UserProfileUpdate`, 400 si vacío); PUT `/auth/me/password` valida contraseña actual (`PasswordChange`, bcrypt)
- `actualizar_perfil` / `cambiar_contrasena` in `bd/crud/user.py` — **convierten `user_id` str → `UUID`** antes de `session.get` (User.id es UUID)
- `/datos/backup` GET → SQLite `src.backup(dst)` a archivo temporal + `FileResponse` (se auto-elimina vía `BackgroundTask`)
- `/datos/restaurar` POST multipart (`UploadFile`) → valida header SQLite, `engine.dispose()`, reemplaza `database.db`, `PRAGMA integrity_check`
- `python-multipart` añadido a `requirements.txt` (necesario para `UploadFile`)
- Frontend: botones backup/restaurar activos en `ajustes.html`, helpers `downloadFile()`/`uploadFile()` en `funciones.js`

## Key refactors (Fase 5 — Frontend conectado, en curso)

- Token storage unified: `guardarToken()`, `obtenerToken()`, `cerrarSesion()` in `funciones.js`
- Bearer token auto-injected in every `request()` via `Authorization` header (except `PUBLIC_PATHS`)
- `health/token` changed from query-param to `Depends(validate_token)` (Bearer)
- `funciones.js` cleaned: removed demo event listeners, unused `get()` `data` param (127 lines)

## Notable quirks

- `User.id` is `uuid.UUID`; other model PKs are `int`.
- Password hashing uses `passlib.hash.bcrypt`.
- `Movimiento.es_ingreso` inferred from `monto > 0`.
- Tailwind configured via inline `<script>` in `index.html` (no build step).
- Frontend uses `sessionStorage` for token (key: `auth_token`) and `localStorage` for `remember_session` flag.
- `obtener_usuario_por_token()` only checks the **first** `Sesion` row → single active session by design; isolation tests log in users sequentially.

## Tests (Fase 6)

- `pytest` + `httpx` + `ruff` in `requirements-dev.txt`; config in `pyproject.toml`.
- `tests/conftest.py` sets `os.environ["APPDATA"]` to a temp dir **before** importing app modules, so the global `engine` binds to a temp SQLite; an autouse `reset_db` fixture drops/recreates schema + seeds per test.
- API tests (`test_auth`, `test_cuentas`, `test_movimientos`, `test_aislamiento`) use `TestClient`; unit tests (`test_movimiento_unit`) call `bd/crud/*` directly (saldo + `ResumenMensual`).
- Dates sent to the API use `dd-mm-YYYY` (parsed by `DateFromString`).
- Lint is scoped to `tests/` + `api/mainApi.py` (ruff `select = ["E", "F", "I"]`).

## Key refactors (Fase 7 — Reportes y análisis)

- `POST /movimientos/importar` recibe `{"filas": [MovimientoImport]}` y crea movimientos en bulk (`crear_movimientos_bulk` en `bd/crud/movimiento.py`); devuelve `{"importados", "errores": [{"fila", "error"}]}` — sin auto-rollback, el usuario decide.
- DTO `MovimientoImport` (monto, fecha, tipo_id, cuenta_id, descripcion) en `api/routers/dtos/movimientoDto.py`.
- Dashboard: card "Flujo Neto Mensual" (ingresos - gastos del mes, verde/rojo según signo).
- Transacciones: filtros por cuenta + rango de fecha (`filtroCuenta`, `filtroDesde`, `filtroHasta` → query params `cuenta_id`, `fecha_desde`, `fecha_hasta`), botones Exportar CSV (descarga con BOM UTF-8 para Excel) e Importar CSV (mapea nombres de cuenta/tipo → ids, acepta fechas ISO o `dd-mm-YYYY`).

## What's missing / planned

See `porHacer.md` for full roadmap. Priority items: connect all web pages to real API, add tests (suggested: pytest with temp SQLite DB).

## MCP Knowledge Graph (codebase-memory-mcp)

El proyecto usa un grafo de conocimiento MCP (`codebase-memory-mcp`) para responder consultas estructurales sin leer archivos uno por uno.

**Regla:** Antes de usar `Grep`/`Glob`/`Read`, consultar primero el grafo MCP.

### Helper (portable)

El script `tools/mcp.py` es portable: se para en el directorio raíz de cualquier proyecto indexado y funciona automáticamente. También puedes copiarlo a `%USERPROFILE%\.local\bin\mcp.py` para usarlo globalmente.

```powershell
# Desde el directorio del proyecto (auto-detecta)
python ruta/a/tools/mcp.py search <patron>
python ruta/a/tools/mcp.py query "<cypher>"
python ruta/a/tools/mcp.py trace <funcion>
python ruta/a/tools/mcp.py arch
python ruta/a/tools/mcp.py code <patron>
python ruta/a/tools/mcp.py schema
python ruta/a/tools/mcp.py projects
python ruta/a/tools/mcp.py index   # re-indexar

# Para otro proyecto (por nombre)
python ruta/a/tools/mcp.py -p Otro-Proyecto search "class .*"
```

### Consultas Cypher útiles

```cypher
MATCH (f:Function) RETURN f.name, f.file_path, f.signature LIMIT 20
MATCH (c:Class) RETURN c.name, c.file_path
MATCH ()-[r:CALLS]->() RETURN r.callee, count(*) as calls ORDER BY calls DESC
MATCH (f:Function {is_entry_point: true}) RETURN f.name, f.file_path
```

### Info de contacto

- El MCP server usa SQLite en `~/.cache/codebase-memory-mcp/`
- Auto-sync: el watcher detecta cambios automáticamente
- `-p <project>` sobreescribe el proyecto autodetectado

## What's missing / planned

See `porHacer.md` for full roadmap. Priority items: connect all web pages to real API, add tests (suggested: pytest with temp SQLite DB).
