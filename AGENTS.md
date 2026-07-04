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
- **Session:** `obtener_sesion()` reads global single session row from DB — not user-scoped. CRUD functions call this directly (tight coupling).
- `database.db` is gitignored; auto-created on first run.

## Recent renames (Fase 0)

- `bd/models/registro.py` → `bd/models/movimiento.py` (class `Registro` → `Movimiento`)
- `bd/crud/registro.py` → `bd/crud/movimiento.py` (`crear_registro` → `crear_movimiento`, `registros_paginados` → `movimientos_paginados`)
- `api/routers/gastos.py` → `api/routers/movimientos.py` (prefix `/gastos` → `/movimientos`)
- `menus/gastos.py` → `menus/movimientos.py` (legacy CLI)
- Relationships: `Cuenta.registros`, `Tipo.registros`, `User.registros` → `movimientos`
- DB table: `registro` → `movimiento` (updated in alembic baseline + APP_TABLES)

## Notable quirks

- Several routers reassign `router` twice (`router = APIRouter()` then `router = APIRouter(prefix=...)`).
- `/movimientos` router is a stub — only returns `"hola"`.
- `User.id` is `uuid.UUID`; other model PKs are `int`.
- Password hashing uses `passlib.hash.bcrypt`.
- `Movimiento.es_ingreso` inferred from `monto > 0`.
- Tailwind configured via inline `<script>` in `index.html` (no build step).
- Frontend uses `localStorage` for `remember_session` flag and `sessionStorage` for token.
- No tests, no lint/format/typecheck config, no CI.

## What's missing / planned

See `porHacer.md` for full roadmap. Priority items: complete movimientos CRUD, connect all web pages to real API, add tests (suggested: pytest with temp SQLite DB), move `database.db` to `%APPDATA%/FlujoCaja/`.
