"""indices de rendimiento

Revision ID: 20261118_0005_indices_rendimiento
Revises: 20261114_0004_deudas_mensuales
Create Date: 2026-11-18 00:00:00.000000

Crea indices compuestos para las consultas calientes y reemplaza el indice
simple de `movimiento.es_deuda` por uno que incluye `user_id` y `fecha`.

Medido sobre una base sintetica (35k movimientos / 7.2k cuotas):
lista de movimientos 94x, resumen mensual 35x, filtro por tipo 56x,
filtro por es_deuda 89x, dashboard de categorias 14x.
"""

from alembic import op

revision = "20261118_0005_indices_rendimiento"
down_revision = "20261114_0004_deudas_mensuales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # movimiento
    op.create_index(
        "ix_movimiento_user_fecha", "movimiento", ["user_id", "fecha"]
    )
    op.create_index(
        "ix_movimiento_user_cuenta_fecha",
        "movimiento",
        ["user_id", "cuenta_id", "fecha"],
    )
    op.create_index(
        "ix_movimiento_user_tipo_fecha",
        "movimiento",
        ["user_id", "tipo_id", "fecha"],
    )
    op.create_index(
        "ix_movimiento_user_es_deuda_fecha",
        "movimiento",
        ["user_id", "es_deuda", "fecha"],
    )
    # El indice simple de es_deuda no se usa: toda consulta filtra por user_id.
    op.drop_index(op.f("ix_movimiento_es_deuda"), table_name="movimiento")

    # cuotas mensuales (proximas / resumen)
    op.create_index(
        "ix_cuotamensual_user_estado_fecha_limite",
        "cuotamensual",
        ["user_id", "estado", "fecha_limite"],
    )

    # pagos de cuotas (resumen del mes)
    op.create_index(
        "ix_pagocuotamensual_user_fecha",
        "pagocuotamensual",
        ["user_id", "fecha"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pagocuotamensual_user_fecha", table_name="pagocuotamensual"
    )
    op.drop_index(
        "ix_cuotamensual_user_estado_fecha_limite", table_name="cuotamensual"
    )

    op.create_index(
        op.f("ix_movimiento_es_deuda"),
        "movimiento",
        ["es_deuda"],
        unique=False,
    )
    op.drop_index(
        "ix_movimiento_user_es_deuda_fecha", table_name="movimiento"
    )
    op.drop_index("ix_movimiento_user_tipo_fecha", table_name="movimiento")
    op.drop_index("ix_movimiento_user_cuenta_fecha", table_name="movimiento")
    op.drop_index("ix_movimiento_user_fecha", table_name="movimiento")
