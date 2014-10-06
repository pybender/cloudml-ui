from api.models import Tag


# TODO: Refactore
def get_tags_list(old_tags, tags):
    existing_tags = [t.text for t in Tag.query.all()]
    tags_to_create = list(set(tags) - set(existing_tags))
    for text in tags_to_create:
        tag = Tag(text=text)
        tag.save()
    return Tag.query.filter(Tag.text.in_(tags)).all()


def recalculate_tags_size(tags, old_tags, models=True, handlers=False):
    for text in list(set(tags + old_tags)):
        tag = Tag.query.filter_by(text=text).one()
        if models:
            tag.count = len(tag.models)
        if handlers:
            tag.handlers_count = len(tag.xml_import_handlers)
        print tag.text, tag.count, tag.handlers_count
        tag.save()
