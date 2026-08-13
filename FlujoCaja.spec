# -*- mode: python ; coding: utf-8 -*-
# Especificación de PyInstaller para FlujoCaja (one-dir).
# Build: .\build.ps1  (o: python -m PyInstaller FlujoCaja.spec)

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
for _pkg in [
    "uvicorn",
    "alembic",
    "sqlalchemy",
    "sqlmodel",
    "pydantic",
    "passlib",
    "bcrypt",
    "rich",
    "multipart",
]:
    hiddenimports += collect_submodules(_pkg)

datas = [
    ("web", "web"),
    ("alembic", "alembic"),
    ("alembic.ini", "."),
    ("assets", "assets"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "menus",
        "widget",
        "app",
        "tests",
        "pytest",
        "httpx",
        "ruff",
        "sklearn",
        "scipy",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="FlujoCaja",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=["assets/icon.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FlujoCaja",
)