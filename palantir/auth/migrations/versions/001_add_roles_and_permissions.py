"""Add roles and permissions

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add roles and permissions columns to user table
    op.add_column('user', sa.Column('roles', sa.JSON(), nullable=False, server_default='["user"]'))
    op.add_column('user', sa.Column('permissions', sa.JSON(), nullable=False, server_default='[]'))

    # Create initial admin user if not exists
    connection = op.get_bind()
    user_table = sa.Table(
        'user',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('roles', sa.JSON),
    )
    
    # Update existing users to have default role
    connection.execute(
        user_table.update().where(
            user_table.c.roles.is_(None)
        ).values(
            roles=['user']
        )
    )


def downgrade():
    # Remove roles and permissions columns
    op.drop_column('user', 'permissions')
    op.drop_column('user', 'roles') 