"""normaliza user.id al formato de texto con guiones

Revision ID: 20261120_0006_user_id_texto
Revises: 20261118_0005_indices_rendimiento
Create Date: 2026-11-20 00:00:00.000000

SQLAlchemy guardaba `user.id` (tipo `Uuid`) como 32 caracteres hex sin
guiones, mientras que todas las columnas `user_id` guardan `str(uuid)` con
guiones. Al activar `PRAGMA foreign_keys=ON` (Fase 11.4) cualquier INSERT en
cuenta/movimiento/... fallaba con `FOREIGN KEY constraint failed`.

Esta migracion reescribe los ids existentes con guiones y cambia el tipo de
la columna a VARCHAR(36), el mismo formato que usan las claves foraneas. El
downgrade hace lo inverso sobre el id y las columnas relacionadas.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261120_0006_user_id_texto"
down_revision = "20261118_0005_indices_rendimiento"
branch_labels = None
depends_on = None

# (tabla, columna) que referencian al usuario y guardan str(uuid).
COLUMNAS_USUARIO = [
    ("sesion", "idUser"),
    ("cuenta", "user_id"),
    ("movimiento", "user_id"),
    ("resumenmensual", "user_id"),
    ("entidad", "user_id"),
    ("deuda", "user_id"),
    ("pagodeuda", "user_id"),
    ("deudamensual", "user_id"),
    ("cuotamensual", "user_id"),
    ("pagocuotamensual", "user_id"),
]

ID_CON_GUIONES = (
    "substr({col}, 1, 8) || '-' || substr({col}, 9, 4) || '-' || "
    "substr({col}, 13, 4) || '-' || substr({col}, 17, 4) || '-' || "
    "substr({col}, 21, 12)"
)


def _normalizar(tabla: str, columna: str, con_guiones: bool) -> None:
    col = f'"{columna}"'
    if con_guiones:
        expresion = ID_CON_GUIONES.format(col=col)
        largo_origen = 32
    else:
        expresion = f"replace({col}, '-', '')"
        largo_origen = 36

    op.execute(
        sa.text(
            f'UPDATE "{tabla}" SET {col} = {expresion} '
            f"WHERE length({col}) = {largo_origen}"
        )
    )


def upgrade() -> None:
    # El id del usuario primero: las columnas hijas ya guardan str(uuid) con
    # guiones, pero se normalizan igual para bases creadas por otras vias.
    _normalizar("user", "id", con_guiones=True)
    for tabla, columna in COLUMNAS_USUARIO:
        _normalizar(tabla, columna, con_guiones=True)

    with op.batch_alter_table("user") as batch:
        batch.alter_column(
            "id",
            type_=sa.String(36),
            existing_type=sa.Uuid(),
            existing_nullable=False,
        )


def downgrade() -> None:
    for tabla, columna in COLUMNAS_USUARIO:
        _normalizar(tabla, columna, con_guiones=False)
    _normalizar("user", "id", con_guiones=False)

    with op.batch_alter_table("user") as batch:
        batch.alter_column(
            "id",
            type_=sa.Uuid(),
            existing_type=sa.String(36),
            existing_nullable=False,
        )
