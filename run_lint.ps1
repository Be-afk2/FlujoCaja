$ErrorActionPreference = "Stop"
venv\Scripts\python.exe -m ruff check tests api/mainApi.py
