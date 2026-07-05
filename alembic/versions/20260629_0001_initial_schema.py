"""initial schema baseline

Revision ID: 20260629_0001_initial_schema
Revises:
Create Date: 2026-06-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260629_0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tipo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tipocuenta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "moneda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("simbolo", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("apellido", sa.String(), nullable=False),
        sa.Column("passw", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subtipo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sesion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idUser", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cuenta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("saldo", sa.Float(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.Column("moneda_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipocuenta.id"]),
        sa.ForeignKeyConstraint(["moneda_id"], ["moneda.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "movimiento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("es_ingreso", sa.Boolean(), nullable=False),
        sa.Column("tipo_id", sa.Integer(), nullable=False),
        sa.Column("subtipo_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo.id"]),
        sa.ForeignKeyConstraint(["subtipo_id"], ["subtipo.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["cuenta_id"], ["cuenta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("movimiento")
    op.drop_table("cuenta")
    op.drop_table("sesion")
    op.drop_table("subtipo")
    op.drop_table("user")
    op.drop_table("moneda")
    op.drop_table("tipocuenta")
    op.drop_table("tipo")
