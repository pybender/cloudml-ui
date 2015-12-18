from flask.ext.testing import TestCase
from api.base.test_utils import BaseDbTestCase

from api import app
from api.base.forms.fields import *
from api.import_handlers.fixtures import XmlImportHandlerData


class FormFieldsTests(TestCase):
    """ Tests of the Form fields: CharField, BooleanField, etc. """
    def create_app(self):
        return app

    def test_base_field(self):
        field = BaseField()
        self.assertEquals(field.clean(1), 1)
        self.assertEquals(field.clean('str'), 'str')

    def test_char_field(self):
        field = CharField()
        self.assertEquals(field.clean('str'), 'str')

    def test_boolean_field(self):
        field = BooleanField()
        self.assertTrue(field.clean(True))
        self.assertTrue(field.clean('True'))
        self.assertTrue(field.clean('true'))
        self.assertTrue(field.clean('1'))
        self.assertTrue(field.clean(u'1'))
        self.assertTrue(field.clean(1))

        self.assertFalse(field.clean(False))
        self.assertFalse(field.clean('0'))
        self.assertFalse(field.clean('False'))

    def test_integer_field(self):
        field = IntegerField()
        self.assertEquals(field.clean(1), 1)
        self.assertEquals(field.clean('1'), 1)
        self.assertRaises(ValidationError, field.clean, '1.0')

    def test_choice_field(self):
        COLORS = ['red', 'green', 'blue']
        field = ChoiceField(choices=COLORS)
        for color in COLORS:
            self.assertEquals(field.clean(color), color)
        self.assertRaises(ValidationError, field.clean, 'magenta')

    def test_json_field(self):
        import json
        data = {'key': 'value'}
        field = JsonField()
        self.assertEquals(field.clean(json.dumps(data)), data)
        self.assertRaises(ValidationError, field.clean, 'invalid json')

    def test_import_handler_file_field(self):
        from api.import_handlers.fixtures import IMPORTHANDLER
        field = ImportHandlerFileField()

        value = field.clean(IMPORTHANDLER)
        self.assertEquals(field.import_handler_type, 'xml')

        # Checking with invalid data
        self.assertRaises(ValidationError, field.clean, '{"key": "value"}')
        self.assertRaises(ValidationError, field.clean, '<plan></plan>')

    def test_features_field(self):
        from api.ml_models.fixtures import FEATURES_CORRECT, FEATURES_INCORRECT
        field = FeaturesField()
        value = field.clean(FEATURES_CORRECT)
        self.assertEquals(value, json.loads(FEATURES_CORRECT))
        self.assertRaises(ValidationError, field.clean, FEATURES_INCORRECT)
        self.assertRaises(ValidationError, field.clean, "some invalid data")
        self.assertRaises(ValidationError, field.clean, '4')
        self.assertRaises(ValidationError, field.clean, '{}')
        self.assertRaises(ValidationError, field.clean, '')

    def test_script_file_field(self):
        field = ScriptFileField()
        value = field.clean('2+2')
        self.assertEqual(value, '2+2')
        self.assertRaises(ValidationError, field.clean, 'invalid code')

    def test_script_url_field(self):
        field = ScriptUrlField()
        value = field.clean('./api/import_handlers/fixtures/functions.py')
        self.assertEqual(value, './api/import_handlers/fixtures/functions.py')
        self.assertRaises(ValidationError, field.clean, 'incorrect/path.py')
        self.assertRaises(ValidationError, field.clean,
                          './api/import_handlers/fixtures/bad_functions.py')


class TestDbFields(BaseDbTestCase):
    datasets = [XmlImportHandlerData]

    def test_model_field(self):
        from api.import_handlers.models import XmlImportHandler
        handler = XmlImportHandler.query.get(1)

        field = ModelField(model=XmlImportHandler, return_model=True)
        self.assertEquals(field.clean(handler.id), handler)
        self.assertRaises(ValidationError, field.clean, 100000)

        field = ModelField(model=XmlImportHandler, return_model=False)
        self.assertEquals(field.clean(handler.id), handler.id)
        self.assertEquals(field.model, handler)

        self.assertEquals(field.clean(None), None)

    # TODO: do we need to raise exc when something not found?
    def test_multiple_model_field(self):
        from api.import_handlers.models import XmlImportHandler
        handlers = XmlImportHandler.query.all()
        handler1, handler2 = handlers[0], handlers[1]
        field = MultipleModelField(model=XmlImportHandler, return_model=True)

        self.assertItemsEqual(
            field.clean('%s,%s' % (handler1.id, handler2.id)),
            [handler1, handler2])
        # TODO: is it rigth behaviour?
        self.assertRaises(ValidationError, field.clean, '200000,10000')
