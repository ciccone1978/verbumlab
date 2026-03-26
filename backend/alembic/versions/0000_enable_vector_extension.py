"""enable vector extension

Revision ID: 0000
Revises: 
Create Date: 2026-03-26 12:08:29.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS vector;")
