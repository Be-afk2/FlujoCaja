# FlujoCaja — Avisos de terceros (Third-party notices)

FlujoCaja distribuye componentes de terceros. Este documento lista cada uno,
su licencia y dónde se encontrará el texto completo.

**Estado de uso actual:** uso personal/local (sin distribución pública del
`.exe`). Si en el futuro se distribuye la aplicación a terceros, ver la
sección [Distribución](#distribución) al final y `planes/PySide6-migracion.md`.

Texto de las licencias presentes en este repositorio:

- `web/fonts/OFL.txt` — SIL Open Font License 1.1
- `web/fonts/LICENSE-MaterialSymbols.txt` — Apache License 2.0
- `web/vendor/fontawesome/LICENSE.txt` — Font Awesome Free (CC BY 4.0 + OFL 1.1 + MIT)
- `web/vendor/tailwind_LICENSE.txt` — MIT (Tailwind CSS)
- `licenses/GPL-3.0.txt` — GNU GPL v3 (stack PyQt6; requerido si se distribuye)
- `licenses/LGPL-3.0.txt` — GNU LGPL v3 (binarios Qt; requerido si se distribuye)

---

## 1. Python — runtime de la aplicación

| Componente | Versión | Licencia (SPDX) | Derechos de autor / Fuente |
|---|---|---|---|
| FastAPI | 0.136.1 | MIT | © 2018 Sebastián Ramírez — https://fastapi.tiangolo.com |
| Uvicorn | 0.46.0 | BSD-3-Clause | https://www.uvicorn.org |
| Starlette | 1.0.0 | BSD-3-Clause | https://www.starlette.io |
| Pydantic | 2.13.3 | MIT | © 2017-2025 Pydantic Services Inc. — https://github.com/pydantic/pydantic |
| pydantic-core | 2.46.3 | MIT | https://github.com/pydantic/pydantic-core |
| SQLModel | 0.0.38 | MIT | © 2018 Sebastián Ramírez — https://sqlmodel.tiangolo.com |
| SQLAlchemy | 2.0.49 | MIT | © 2005-2025 SQLAlchemy — https://www.sqlalchemy.org |
| Alembic | 1.14.1 | MIT | https://alembic.sqlalchemy.org |
| Mako | (transitiva) | MIT | © 2006-2025 Michael Bayer — https://www.makotemplates.org |
| passlib | 1.7.4 | BSD-3-Clause | © 2008-2021 Assurance Technologies — https://passlib.readthedocs.io |
| bcrypt | 4.0.1 | MIT (binding) | © 2003-2025 pyca — https://github.com/pyca/bcrypt |
| python-multipart | 0.0.20 | Apache-2.0 | https://github.com/Kludex/python-multipart |
| rich | 15.0.0 | MIT | © Will McGugan — https://github.com/Textualize/rich |
| Pygments | 2.20.0 | BSD-2-Clause | © 2006-2025 Georg Brandl et al. — https://pygments.org |
| click | 8.3.3 | BSD-3-Clause | © 2014 Pallets — https://palletsprojects.com/p/click |
| questionary | 2.0.1 | MIT | https://github.com/tmbo/questionary |
| anyio | 4.13.0 | MIT | — https://anyio.readthedocs.io |
| h11 | 0.16.0 | MIT | https://github.com/python-hyper/h11 |
| idna | 3.13 | BSD-3-Clause | © 2013-2025 Kim Davies — https://github.com/kjd/idna |
| markdown-it-py | 4.0.0 | MIT | https://github.com/executablebooks/markdown-it-py |
| mdurl | 0.1.2 | MIT | https://github.com/executablebooks/mdurl |
| colorama | 0.4.6 | BSD-3-Clause | © 2013-2022 Jonathan Hartley — https://github.com/tartley/colorama |
| annotated-types | 0.7.0 | MIT | — |
| annotated-doc | 0.0.4 | MIT | — |
| typing-inspection | 0.4.2 | MIT | — |
| typing_extensions | 4.15.0 | PSF-2.0 | © Python Software Foundation |

## 2. GUI — PyQt6 y Qt6 (WebEngine)

> ⚠ **Importante:** estos componentes se copian dentro del `.exe`. La
> licencia de los bindings PyQt (GPL-3.0) hoy no genera obligaciones porque
> la app no se distribuye; ver [Distribución](#distribución).

| Componente | Versión | Licencia | Notas |
|---|---|---|---|
| PyQt6 | 6.11.0 | GPL-3.0-only **o** licencia comercial (Riverbank) | Binding — https://www.riverbankcomputing.com/software/pyqt/ |
| PyQt6-WebEngine | 6.11.0 | GPL-3.0-only **o** licencia comercial (Riverbank) | Binding WebEngine |
| PyQt6_sip | 13.11.1 | GPL-3.0-only **o** comercial (Riverbank) | https://www.riverbankcomputing.com/software/sip/ |
| PyQt6-Qt6 | 6.11.0 | LGPL-3.0 | Binarios Qt (QtCore/Gui/Widgets) |
| PyQt6-WebEngine-Qt6 | 6.11.0 | LGPL-3.0 | Binarios Qt WebEngine (Chromium) |

## 3. Herramienta de empaquetado

| Componente | Versión | Licencia | Notas |
|---|---|---|---|
| PyInstaller | 6.22.0 | GPL-2.0-or-later **con excepción** | El ejecutable generado no hereda GPL — https://pyinstaller.org |
| pyinstaller-hooks-contrib | 2026.6 | Apache-2.0 | https://github.com/pyinstaller/pyinstaller-hooks-contrib |

## 4. Assets web vendoreados (se incluyen en el `.exe`)

| Componente | Dónde | Licencia | Texto |
|---|---|---|---|
| Tailwind CSS (play CDN standalone) | `web/vendor/tailwind.js` | MIT | `web/vendor/tailwind_LICENSE.txt` |
| Font Awesome Free 6.4.0 | `web/vendor/fontawesome/` | Icons: **CC BY 4.0** · Fuentes: **SIL OFL 1.1** · Código: **MIT** | `web/vendor/fontawesome/LICENSE.txt` |
| Material Symbols Outlined | `web/fonts/material-symbols-*.woff2` | Apache-2.0 | `web/fonts/LICENSE-MaterialSymbols.txt` |
| Hanken Grotesk | `web/fonts/hanken-grotesk-*.woff2` | SIL OFL 1.1 | `web/fonts/OFL.txt` |
| Inter | `web/fonts/inter-*.woff2` | SIL OFL 1.1 | `web/fonts/OFL.txt` |
| JetBrains Mono | `web/fonts/jetbrains-mono-*.woff2` | SIL OFL 1.1 | `web/fonts/OFL.txt` |
| Public Sans | `web/fonts/public-sans-*.woff2` | SIL OFL 1.1 | `web/fonts/OFL.txt` |
| Noto Sans | `web/fonts/noto-sans-*.woff2` | SIL OFL 1.1 | `web/fonts/OFL.txt` |

Notas sobre atribución:

- **Font Awesome:** el `all.min.css` descargado conserva el encabezado
  `/*! Font Awesome Free 6.4.0 ... */` con la atribución (CC BY 4.0 · OFL 1.1 ·
  MIT). No debe eliminarse. Sitio oficial: https://fontawesome.com/license/free
- **Material Symbols:** iconos de Google bajo Apache 2.0; el texto de licencia
  se incluye junto a las fuentes.
- **Fuentes OFL:** se permite embeber las fuentes en la app; el texto OFL debe
  acompañar a las fuentes (ya incluido). Prohibido redistribuirlos como
  producto independiente.

## 5. Generado por el proyecto

- `assets/icon.ico`, `assets/icon.png`, `assets/icon-small.png` — creados por
  `scripts/generar_icono.py` (dominio de FlujoCaja; sin licencias de terceros).

---

## Distribución

Si el `.exe` se llega a **distribuir a terceros**, antes se debe:

1. **Decidir la ruta de licencia del GUI** (ver `planes/PySide6-migracion.md`):
   - **Opción A — mantener PyQt6 (GPL):** el conjunto distribuido queda bajo
     GPL-3.0 → ofrecer/dejar disponible el código fuente de la app (GPL §4-5).
   - **Opción B — migrar a PySide6 (LGPL-3.0):** permite distribuirlo cerrado.
2. **Incluir al distribuir:**
   - `licenses/GPL-3.0.txt` y/o `licenses/LGPL-3.0.txt` (según stack final).
   - Este `THIRD_PARTY_NOTICES.md` (ya lo copia `build.ps1` junto al exe).
   - Los textos OFL/Apache/FA/MIT de `web/` (ya dentro del paquete).
   - En LGPL: aviso prominente del uso de Qt + instalación justa p/ re-enlazar.