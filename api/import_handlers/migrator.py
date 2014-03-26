import logging
import re
import json
from models import ImportHandler, XmlImportHandler, db, XmlDataSource, \
    XmlEntity, XmlQuery, XmlField, XmlInputParameter, XmlScript

DATASOURCE_PARAMS_REGEX = re.compile("((\w+)=['\"]+(\w+)['\"]+)", re.VERBOSE)


def xml_migrate():
#    XmlImportHandler.query.delete()
    logging.info('Start migrations')
    for json_handler in ImportHandler.query.all():
        logging.info('Processing json import handler %s:%s',
                     json_handler.name, json_handler.id)
        data = json_handler.data
        if data is None:
            logging.warning('json import handler %s:%s is empty',
                            json_handler.name, json_handler.id)
            continue
        handler = XmlImportHandler(name=json_handler.name + '3')
        db.session.add(handler)

        logging.info('Parsing datasources')
        for ds_data in data['datasource']:
            ds = XmlDataSource(
                name=ds_data['name'],
                import_handler=handler,
                type=get_datasource_type(ds_data['type']),
                params=get_datasource_params(ds_data))
            db.session.add(ds)

        logging.info('Parsing queries')
        for query_data in data['queries']:
            from core.importhandler.importhandler import ExtractionPlan
            plan = ExtractionPlan(json.dumps(data), is_file=False)
            for name in plan.input_params:
                param = XmlInputParameter(
                    import_handler=handler,
                    name=name,
                    type='string')
                db.session.add(param)
            print "working with %s" % json_handler.id
            sql = get_query_text(query_data['sql'], plan.input_params)
            query_obj = XmlQuery(text=sql)
            entity = XmlEntity(
                name=query_data['name'],
                import_handler=handler,
                query_obj=query_obj,
                datasource=ds)
            db.session.add(entity)
            # Adding scripts for composite type
            script = XmlScript(import_handler=handler, data="""
def composite_string(expression_value, value):
    res = expression_value % value
    return res.decode('utf8', 'ignore')

def composite_python(expression_value, value):
    res = composite_string(expression_value, value)
    return eval(res)

def composite_readability(expression_value, value):
    res = composite_string(expression_value, value)
    return res

""")
            script = XmlScript()
            for item_data in query_data['items']:
                process_as = item_data.get('process_as', 'string')
                if process_as == 'identity':
                    raise Exception(
                        'No corresponding type for identity process_as')
                if process_as in ('string', 'float',
                                  'boolean', 'integer'):
                    # Simple field
                    name = item_data['target_features'][0]['name']
                    field = XmlField(
                        name=name,
                        column=item_data['source'],
                        type=process_as)
                    db.session.add(field)
                    entity.fields.append(field)
                if process_as == 'json':
                    tr_field = XmlField(
                        name=item_data['source'],
                        column=item_data['source'],
                        transform='json')
                    db.session.add(tr_field)
                    entity.fields.append(tr_field)
                    sub_entity = XmlEntity(
                        name=item_data['source'],
                        entity=entity,
                        transformed_field=tr_field)
                    db.session.add(sub_entity)
                    for feature_data in item_data['target_features']:
                        field = XmlField(
                            name=feature_data['name'],
                            jsonpath=feature_data['jsonpath'])
                        # TODO: think about key_path, value_path
                        if feature_data.get('to_csv'):
                            field.join = ','
                        db.session.add(field)
                        sub_entity.fields.append(field)
                if process_as == 'composite':
                    for feature in item_data['target_features']:
                        expression_type = feature['expression']['type']
                        expression_value = feature['expression']['value']
                        if expression_type == 'string':
                            script_text = 'composite_string(%s, #{value})' % expression_value
                            field = XmlField(
                                name=feature['name'],
                                script=script_text)
                        elif expression_type == 'python':
                            script_text = 'composite_python(%s, #{value})' % expression_value
                            field = XmlField(
                                name=feature['name'],
                                script=script_text)
                        elif expression_type == 'readability':
                            script_text = 'composite_readability(%s, #{value})' % expression_value
                            field = XmlField(
                                name=feature['name'],
                                script=script_text)
            handler.update_import_params()
        db.session.commit()


def get_datasource_type(json_type):
    if json_type == 'sql':
        return 'db'
    if json_type == 'request':
        return 'http'
    raise ValueError('JSON datasource type %s not found' % json_type)


def get_datasource_params(data):
    if data['type'] == 'sql':
        db_data = data['db']
        params = {'vendor': db_data['vendor']}
        conn = db_data['conn']
        for item in DATASOURCE_PARAMS_REGEX.findall(conn):
            params[item[1]] = item[2]
        logging.info('Parsing conn string %s. Got %s', conn, params)
        return params
    else:
        raise Exception('Not implemented')


def get_query_text(text, input_params):
    if not isinstance(text, basestring):
        text = text[0]
    for param in input_params:
        text = text.replace("%({0})s".format(param), "#{%s}" % param)
    return text
