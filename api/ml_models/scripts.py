from api.ml_models.models import Tag


def recalculate_tags_counters():
    """Recalculates counter value for all model tags"""
    tags = Tag.query.all()
    for tag in tags:
        tag.update_counter()
