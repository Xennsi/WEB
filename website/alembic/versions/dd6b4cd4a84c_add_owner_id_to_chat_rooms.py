"""Add owner_id to chat_rooms

Revision ID: dd6b4cd4a84c
Revises: 
Create Date: 2024-10-28 01:09:15.929994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd6b4cd4a84c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat_rooms', sa.Column('owner_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'chat_rooms', 'users', ['owner_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'chat_rooms', type_='foreignkey')
    op.drop_column('chat_rooms', 'owner_id')
    # ### end Alembic commands ###
