from __future__ import annotations

"""
Migration initiale.

Workflows documentés
--------------------

Cas nominal
- Crée la table `users` avec un `id` ULID (26 chars), un email unique, et des timestamps.

Cas d'exception
- Si la table existe déjà, Alembic lèvera (ce qui est attendu : on ne rejoue pas une migration).
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("users_email_unique", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("users_email_unique", table_name="users")
    op.drop_table("users")
