"""add image field to post model

Revision ID: 3cfb3ea12959
Revises: 71d23109ca88
Create Date: 2025-03-02 04:02:08.893505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cfb3ea12959'
down_revision = '71d23109ca88'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=120), nullable=True))
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('summary',
               existing_type=sa.VARCHAR(length=300),
               type_=sa.Text(),
               existing_nullable=True)
        batch_op.drop_column('slug')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.VARCHAR(length=200), nullable=True))
        batch_op.alter_column('summary',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=300),
               existing_nullable=True)
        batch_op.alter_column('title',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
        batch_op.drop_column('image')

    # ### end Alembic commands ###
