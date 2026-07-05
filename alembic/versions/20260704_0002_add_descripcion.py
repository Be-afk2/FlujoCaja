"""add descripcion column to movimiento

Revision ID: 20260704_0002_add_descripcion
Revises: 20260629_0001_initial_schema
Create Date: 2026-07-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0002_add_descripcion"
down_revision = "20260629_0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movimiento", sa.Column("descripcion", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("movimiento", "descripcion")
