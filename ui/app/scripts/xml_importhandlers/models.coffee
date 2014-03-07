angular.module('app.xml_importhandlers.models', ['app.config'])


.factory('XmlImportHandler', [
  'settings'
  'BaseModel'
  
  (settings, BaseModel) ->
    class XmlImportHandler extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/"
      BASE_UI_URL: "/xml_importhandlers/"
      API_FIELDNAME: 'xml_import_handler'
      @LIST_MODEL_NAME: 'xml_import_handlers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,created_on,created_by'
      TYPE: 'XML'

      id: null
      name: null
      created_on: null
      created_by: null

      datasources: []
      input_parameters: []
      scripts: []
      entities: []
      predict: []

    return XmlImportHandler
])