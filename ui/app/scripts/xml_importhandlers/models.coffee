angular.module('app.xml_importhandlers.models', ['app.config'])


.factory('XmlImportHandler', [
  'settings'
  'BaseModel'
  'InputParameter'
  'Entity'
  
  (settings, BaseModel, InputParameter, Entity) ->
    class XmlImportHandler extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/"
      BASE_UI_URL: "/handlers/xml/"
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
      xml_input_parameters: []
      scripts: []
      entities: []
      predict: []

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          defaults = {'import_handler_id': @id}
          if origData.entity?
            @entity = new Entity(_.extend origData.entity, defaults)
          if origData.xml_input_parameters?
            @xml_input_parameters = []
            for paramData in origData.xml_input_parameters
              @xml_input_parameters.push new InputParameter(
                _.extend paramData, defaults)
          
    return XmlImportHandler
])

.factory('Field', [
  'settings'
  'BaseModel'
  
  (settings, BaseModel) ->
    class Field extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/fields/"
      API_FIELDNAME: 'field'
      @LIST_MODEL_NAME: 'fields'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name'

      TYPES_LIST: ['integer', 'boolean', 'string', 'float']
      TRANSFORM_LIST: ['csv', 'json']

      id: null

    return Field
])

.factory('Entity', [
  'settings'
  'BaseModel'
  'Field'
  
  (settings, BaseModel, Field) ->
    class Entity extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/entities/"
      API_FIELDNAME: 'entity'
      @LIST_MODEL_NAME: 'entities'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name'

      id: null
      datasource: null
      datasource_id: null
      datasource_name: null
      fields: []
      import_handler_id: null
      name: null
      query_id: null
      query_obj: null
      entities: []

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          defaults = {
            'import_handler_id': @import_handler_id
            'entity_id': @id
          }
          if origData.fields?
            @fields = []
            for data in origData.fields
              @fields.push new Field(_.extend data, defaults)

          if origData.entities?
            @entities = []
            for data in origData.entities
              @entities.push new Entity(_.extend data, defaults)
    return Entity
])

.factory('InputParameter', [
  'settings'
  'BaseModel'
  
  (settings, BaseModel) ->
    class InputParameter extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/input_parameters/"
      API_FIELDNAME: 'xml_input_parameter'
      @LIST_MODEL_NAME: 'input_parameters'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,regex,format'

      id: null
      type: null
      name: null
      regex: null
      format: null

    return InputParameter
])
