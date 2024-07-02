"""empty message

Revision ID: 4b29ca838f69
Revises: 
Create Date: 2024-06-28 19:29:41.175747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b29ca838f69'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('resume',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('address', sa.String(length=20), nullable=False),
    sa.Column('salary', sa.String(length=20), nullable=False),
    sa.Column('requirement', sa.String(length=200), nullable=False),
    sa.Column('responsibility', sa.String(length=200), nullable=False),
    sa.Column('alternate_url', sa.String(length=200), nullable=True),
    sa.Column('time', sa.String(length=10), nullable=True),
    sa.Column('timeDay', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('resume')
    # ### end Alembic commands ###
