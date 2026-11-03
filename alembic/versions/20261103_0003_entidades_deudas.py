"""entidades y deudas

Revision ID: 20261103_0003_entidades_deudas
Revises: 20260704_0002_add_descripcion
Create Date: 2026-11-03 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "20261103_0003_entidades_deudas"
down_revision = "20260704_0002_add_descripcion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entidad",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_entidad_user_id"), "entidad", ["user_id"], unique=False)

    op.create_table(
        "deuda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=False),
        sa.Column("direccion", sa.String(), nullable=False),
        sa.Column("monto_original", sa.Float(), nullable=False),
        sa.Column("moneda_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("vencimiento", sa.Date(), nullable=True),
        sa.Column("movimiento_inicial_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["entidad_id"], ["entidad.id"]),
        sa.ForeignKeyConstraint(["moneda_id"], ["moneda.id"]),
        sa.ForeignKeyConstraint(["movimiento_inicial_id"], ["movimiento.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deuda_user_id"), "deuda", ["user_id"], unique=False)
    op.create_index(op.f("ix_deuda_entidad_id"), "deuda", ["entidad_id"], unique=False)

    op.create_table(
        "pagodeuda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("deuda_id", sa.Integer(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), nullable=False),
        sa.Column("movimiento_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["deuda_id"], ["deuda.id"]),
        sa.ForeignKeyConstraint(["cuenta_id"], ["cuenta.id"]),
        sa.ForeignKeyConstraint(["movimiento_id"], ["movimiento.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("movimiento_id", name="uq_pagodeuda_movimiento"),
    )
    op.create_index(op.f("ix_pagodeuda_user_id"), "pagodeuda", ["user_id"], unique=False)
    op.create_index(op.f("ix_pagodeuda_deuda_id"), "pagodeuda", ["deuda_id"], unique=False)

    op.add_column(
        "movimiento",
        sa.Column("es_deuda", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index(
        op.f("ix_movimiento_es_deuda"), "movimiento", ["es_deuda"], unique=False
    )

    op.add_column(
        "resumenmensual",
        sa.Column(
            "total_ingresos_deuda",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "resumenmensual",
        sa.Column(
            "total_gastos_deuda",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("resumenmensual", "total_gastos_deuda")
    op.drop_column("resumenmensual", "total_ingresos_deuda")

    op.drop_index(op.f("ix_movimiento_es_deuda"), table_name="movimiento")
    op.drop_column("movimiento", "es_deuda")

    op.drop_index(op.f("ix_pagodeuda_deuda_id"), table_name="pagodeuda")
    op.drop_index(op.f("ix_pagodeuda_user_id"), table_name="pagodeuda")
    op.drop_table("pagodeuda")

    op.drop_index(op.f("ix_deuda_entidad_id"), table_name="deuda")
    op.drop_index(op.f("ix_deuda_user_id"), table_name="deuda")
    op.drop_table("deuda")

    op.drop_index(op.f("ix_entidad_user_id"), table_name="entidad")
    op.drop_table("entidad")
