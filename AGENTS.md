# FlujoCaja — AGENTS.md

## Entrypoints

- `main.py` — main app: starts DB → API (Uvicorn on `127.0.0.1:8000`) → PyQt6 WebEngine desktop window
- `app.py` — legacy CLI, still present under `menus/` and `widget/`

## Run commands

```powershell
venv\Scripts\activate
pip install -r requirements.txt
python main.py                  # full app (BD + API + web)
python main.py --api            # API only
python main.py --api --debug    # API with debug logging
python main.py --bd             # DB init only
python main.py --web            # web shell only
```

## Architecture

- **Backend:** FastAPI (`api/mainApi.py`), routers in `api/routers/`
- **DB:** SQLite (`database.db`), SQLModel (`bd/models/`), CRUD in `bd/crud/`
- **Frontend:** static HTML/JS/Tailwind via CDN in `web/`, loaded by PyQt6 WebEngine
- **Auth:** simple SQLite token (single-session, no JWT). Bearer token via `Authorization` header. Validated against `sesion` table.
  - Unprotected routes: `/auth/*` (login, create, session check, token life)
  - Protected routes (require `Depends(validate_token)`): `/movimientos`, `/tipos`, `/subtipos`, `/cuenta`, `/moneda`
- **Session:** Single session row in DB. Auth via `Authorization: Bearer <token>`, validated by `validate_token()` in `api/dependencies.py` which resolves the `User`. Legacy `obtener_sesion()` still present but deprecated.
- `database.db` is gitignored; auto-created on first run.

## Recent renames (Fase 0)

- `bd/models/registro.py` → `bd/models/movimiento.py` (class `Registro` → `Movimiento`)
- `bd/crud/registro.py` → `bd/crud/movimiento.py` (`crear_registro` → `crear_movimiento`, `registros_paginados` → `movimientos_paginados`)
- `api/routers/gastos.py` → `api/routers/movimientos.py` (prefix `/gastos` → `/movimientos`)
- `menus/gastos.py` → `menus/movimientos.py` (legacy CLI)
- Relationships: `Cuenta.registros`, `Tipo.registros`, `User.registros` → `movimientos`
- DB table: `registro` → `movimiento` (updated in alembic baseline + APP_TABLES)

## Notable quirks

- `User.id` is `uuid.UUID`; other model PKs are `int`.
- Password hashing uses `passlib.hash.bcrypt`.
- `Movimiento.es_ingreso` inferred from `monto > 0`.
- Tailwind configured via inline `<script>` in `index.html` (no build step).
- Frontend uses `localStorage` for `remember_session` flag and `sessionStorage` for token.
- No tests, no lint/format/typecheck config, no CI.

## MCP Knowledge Graph (codebase-memory-mcp)

El proyecto usa un grafo de conocimiento MCP (`codebase-memory-mcp` v0.8.1) para responder consultas estructurales sin leer archivos uno por uno.

**Regla:** Antes de usar `Grep`/`Glob`/`Read`, consultar primero el grafo MCP.

### Helper (portable)

El script `tools/mcp.py` es portable: se para en el directorio raíz de cualquier proyecto
indexado y funciona automáticamente. También puedes copiarlo a `%USERPROFILE%\.local\bin\mcp.py`
para usarlo globalmente.

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
- Indexado por última vez: `2026-07-06T20:17:22Z` — 536 nodos, 1405 aristas
- Auto-sync: el watcher detecta cambios automáticamente
- `-p <project>` sobreescribe el proyecto autodetectado

## What's missing / planned

See `porHacer.md` for full roadmap. Priority items: connect all web pages to real API, add tests (suggested: pytest with temp SQLite DB).
