"""Set up trainer file size

Revision ID: 36ddee11cad
Revises: 2f31710b57ec
Create Date: 2014-01-30 19:02:14.988637

"""

# revision identifiers, used by Alembic.

revision = '36ddee11cad'
down_revision = '2f31710b57ec'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import undefer

from api import app

db = app.sql_db


def upgrade():
    from api.ml_models.models import Model
    for model in Model.query.options(undefer(Model.trainer)).all():
        if not model.trainer_size:
            model.trainer_size = len(model.trainer)
            db.session.add(model)
    db.session.commit()


def downgrade():
    pass
