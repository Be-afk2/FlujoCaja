"""deudas mensuales

Revision ID: 20261114_0004_deudas_mensuales
Revises: 20261103_0003_entidades_deudas
Create Date: 2026-11-14 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "20261114_0004_deudas_mensuales"
down_revision = "20261103_0003_entidades_deudas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deudamensual",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.Column("subtipo_id", sa.Integer(), nullable=True),
        sa.Column("moneda_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("modalidad", sa.String(), nullable=False),
        sa.Column("monto_modo", sa.String(), nullable=False),
        sa.Column("monto_cuota", sa.Float(), nullable=False),
        sa.Column("monto_total", sa.Float(), nullable=True),
        sa.Column("cuotas_totales", sa.Integer(), nullable=True),
        sa.Column("dia_aparicion", sa.Integer(), nullable=False),
        sa.Column("dia_limite", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False),
        sa.Column("fecha_cancelacion", sa.Date(), nullable=True),
        sa.Column("cuenta_pago_default_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["entidad_id"], ["entidad.id"]),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo.id"]),
        sa.ForeignKeyConstraint(["subtipo_id"], ["subtipo.id"]),
        sa.ForeignKeyConstraint(["moneda_id"], ["moneda.id"]),
        sa.ForeignKeyConstraint(
            ["cuenta_pago_default_id"], ["cuenta.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_deudamensual_user_id"),
        "deudamensual",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deudamensual_entidad_id"),
        "deudamensual",
        ["entidad_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deudamensual_estado"),
        "deudamensual",
        ["estado"],
        unique=False,
    )

    op.create_table(
        "cuotamensual",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("deuda_mensual_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("fecha_aparicion", sa.Date(), nullable=False),
        sa.Column("fecha_limite", sa.Date(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False),
        sa.Column("estado_pago", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(
            ["deuda_mensual_id"], ["deudamensual.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "deuda_mensual_id",
            "numero",
            name="uq_cuotamensual_deuda_numero",
        ),
    )
    op.create_index(
        op.f("ix_cuotamensual_user_id"),
        "cuotamensual",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cuotamensual_deuda_mensual_id"),
        "cuotamensual",
        ["deuda_mensual_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cuotamensual_estado"),
        "cuotamensual",
        ["estado"],
        unique=False,
    )

    op.create_table(
        "pagocuotamensual",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("cuota_id", sa.Integer(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), nullable=False),
        sa.Column("movimiento_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["cuota_id"], ["cuotamensual.id"]),
        sa.ForeignKeyConstraint(["cuenta_id"], ["cuenta.id"]),
        sa.ForeignKeyConstraint(["movimiento_id"], ["movimiento.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cuota_id", name="uq_pagocuotamensual_cuota"
        ),
        sa.UniqueConstraint(
            "movimiento_id", name="uq_pagocuotamensual_movimiento"
        ),
    )
    op.create_index(
        op.f("ix_pagocuotamensual_user_id"),
        "pagocuotamensual",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pagocuotamensual_cuota_id"),
        "pagocuotamensual",
        ["cuota_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_pagocuotamensual_cuota_id"),
        table_name="pagocuotamensual",
    )
    op.drop_index(
        op.f("ix_pagocuotamensual_user_id"),
        table_name="pagocuotamensual",
    )
    op.drop_table("pagocuotamensual")

    op.drop_index(
        op.f("ix_cuotamensual_estado"), table_name="cuotamensual"
    )
    op.drop_index(
        op.f("ix_cuotamensual_deuda_mensual_id"),
        table_name="cuotamensual",
    )
    op.drop_index(
        op.f("ix_cuotamensual_user_id"), table_name="cuotamensual"
    )
    op.drop_table("cuotamensual")

    op.drop_index(
        op.f("ix_deudamensual_estado"), table_name="deudamensual"
    )
    op.drop_index(
        op.f("ix_deudamensual_entidad_id"), table_name="deudamensual"
    )
    op.drop_index(
        op.f("ix_deudamensual_user_id"), table_name="deudamensual"
    )
    op.drop_table("deudamensual")
