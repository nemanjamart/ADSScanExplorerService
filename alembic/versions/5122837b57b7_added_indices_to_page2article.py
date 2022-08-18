"""Added indices to page2article

Revision ID: 5122837b57b7
Revises: 2779821beaa2
Create Date: 2022-08-18 16:23:31.854892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5122837b57b7'
down_revision = '2779821beaa2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_page2article_article_id'), 'page2article', ['article_id'], unique=False)
    op.create_index(op.f('ix_page2article_page_id'), 'page2article', ['page_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_page2article_page_id'), table_name='page2article')
    op.drop_index(op.f('ix_page2article_article_id'), table_name='page2article')
    # ### end Alembic commands ###
