def get_data_from_vectorizer(vect_data, feature_name, vectorizer, offset):
    data = {}
    feature_names = vectorizer.get_feature_names()
    for j in range(0, len(feature_names)):
        name = '%s->%s' % (feature_name.replace(".", "->"), feature_names[j])
        data[name] = vect_data[offset + j]
    return data


def get_features_vect_data(vect_data, features, target_variable):
    data = {}
    index = 0

    for feature_name, feature in features:
        if feature_name == target_variable:
            continue

        transformer = feature['transformer']
        preprocessor = feature['type'].preprocessor
        if transformer is not None and hasattr(transformer, 'num_topics'):
            for j in range(0, transformer.num_topics):
                name = '%s->Topic #%d' % (feature_name.replace(".", "->"), j)
                data[name] = vect_data[index + j]
            index += transformer.num_topics
        elif transformer is not None and \
                hasattr(transformer, 'get_feature_names'):
            if hasattr(transformer, 'get_feature_names'):
                data_v = get_data_from_vectorizer(vect_data, feature_name,
                                                  transformer,
                                                  index)
                data.update(data_v)
                index += len(data_v)
            else:
                raise ValueError('Invalid transformer for %s' % feature_name)
        elif preprocessor is not None:
            if hasattr(preprocessor, 'get_feature_names'):
                data_v = get_data_from_vectorizer(vect_data, feature_name,
                                                  preprocessor,
                                                  index)
                data.update(data_v)
                index += len(data_v)
            else:
                raise ValueError('Invalid preprocessor for %s' % feature_name)
        else:
            # Scaler or array
            data[feature_name.replace(".", "->")] = vect_data[index]
            index += 1

    return data
