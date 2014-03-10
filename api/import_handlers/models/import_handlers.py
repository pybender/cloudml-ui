from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declared_attr

from api.base.models import db, BaseModel


class ImportHandlerMixin(BaseModel):
    TYPE = 'N/A'

    @declared_attr
    def name(cls):
        return db.Column(db.String(200), nullable=False, unique=True)

    @declared_attr
    def import_params(cls):
        return db.Column(postgresql.ARRAY(db.String))

    def get_plan_config(self):
        """ Returns config that would be used for creating Extraction Plan """
        return ""

    def get_extraction_plan(self):
        raise Exception('Not implemented')

    def get_fields(self):
        """
        Returns list of the field names
        """
        return []

    def create_dataset(self, params, data_format='json'):
        from data_sets import DataSet
        dataset = DataSet()
        str_params = "-".join(["%s=%s" % item
                               for item in params.iteritems()])
        dataset.name = "%s: %s" % (self.name, str_params)
        dataset.import_handler_id = self.id
        dataset.import_params = params
        dataset.format = data_format
        dataset.save()
        dataset.set_file_path()
        return dataset

    def check_sql(self, sql):
        """
        Parses sql query structure from text,
        raises Exception if it's not a SELECT query or invalid sql.
        """
        import sqlparse

        query = sqlparse.parse(sql)
        wrong_sql = False
        if len(query) < 1:
            wrong_sql = True
        else:
            query = query[0]
            if query.get_type() != 'SELECT':
                wrong_sql = True

        if wrong_sql:
            raise Exception('Invalid sql query')
        else:
            return query

    def build_query(self, sql, limit=2):
        """
        Parses sql query and changes LIMIT statement value.
        """
        import re
        from sqlparse import parse, tokens
        from sqlparse.sql import Token

        # It's important to have a whitespace right after every LIMIT
        pattern = re.compile('limit([^ ])', re.IGNORECASE)
        sql = pattern.sub(r'LIMIT \1', sql)

        query = parse(sql.rstrip(';'))[0]

        # Find LIMIT statement
        token = query.token_next_match(0, tokens.Keyword, 'LIMIT')
        if token:
            # Find and replace LIMIT value
            value = query.token_next(query.token_index(token), skip_ws=True)
            if value:
                new_token = Token(value.ttype, str(limit))
                query.tokens[query.token_index(value)] = new_token
        else:
            # If limit is not found, append one
            new_tokens = [
                Token(tokens.Whitespace, ' '),
                Token(tokens.Keyword, 'LIMIT'),
                Token(tokens.Whitespace, ' '),
                Token(tokens.Number, str(limit)),
            ]
            last_token = query.tokens[-1]
            if last_token.ttype == tokens.Punctuation:
                query.tokens.remove(last_token)
            for new_token in new_tokens:
                query.tokens.append(new_token)

        return str(query)

    def execute_sql_iter(self, sql, datasource_name):
        """
        Executes sql using data source with name datasource_name.
        Datasource with given name should be in handler's datasource list.
        Returns iterator.
        """
        from core.importhandler import importhandler
        datasource = next((d for d in self.data['datasource']
                           if d['name'] == datasource_name))

        iter_func = importhandler.ImportHandler.DB_ITERS.get(
            datasource['db']['vendor'])

        for row in iter_func([sql], datasource['db']['conn']):
            yield dict(row)

    def __repr__(self):
        return '<%s Import Handler %r>' % (self.TYPE, self.name)
