

if __name__ == "__main__":
    # transformer = PredefinedTransformer()
    from api.ml_models.models import Model
    model = Model.query.first()
    trainer = model.get_trainer()
    for feature_name, feature in trainer._feature_model.features.iteritems():
        if feature.get('transformer', None):
            print feature['transformer'].vocabulary_
            break

