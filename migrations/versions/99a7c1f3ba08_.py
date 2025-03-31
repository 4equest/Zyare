"""empty message

Revision ID: 99a7c1f3ba08
Revises: 36d3bf2345cc
Create Date: 2024-03-19 19:34:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '99a7c1f3ba08'
down_revision = '36d3bf2345cc'
branch_labels = None
depends_on = None

def upgrade():
    # 既存のテーブルを削除
    op.drop_table('vote')

    # 新しい構造でテーブルを作成
    op.create_table('vote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('voter_id', sa.Integer(), nullable=False),
        sa.Column('votes', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['room.id'], ),
        sa.ForeignKeyConstraint(['voter_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # 新しいテーブルを削除
    op.drop_table('vote')

    # 元の構造でテーブルを作成
    op.create_table('vote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('voter_id', sa.Integer(), nullable=False),
        sa.Column('vote1', sa.Integer(), nullable=False),
        sa.Column('vote2', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['room.id'], ),
        sa.ForeignKeyConstraint(['voter_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['vote1'], ['user.id'], ),
        sa.ForeignKeyConstraint(['vote2'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

