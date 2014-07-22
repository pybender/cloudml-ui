angular.module('app.xml_importhandlers.models', ['app.config'])

# TODO: create a mixin
# http://coffeescriptcookbook.com/chapters/classes_and_objects/mixins
.factory('BaseImportHandlerItem', [
  'settings'
  'BaseModel'
  
  (settings, BaseModel) ->
    class BaseImportHandlerItem extends BaseModel
      @ITEM_NAME: 'item'

      @$get_api_url: (opts, model) ->
        if model?
          handler_id = model.import_handler_id
        else
          handler_id = opts.import_handler_id

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/#{@ITEM_NAME}/"

      @$beforeLoadAll: (opts) ->
        if not opts.import_handler_id
          throw new Error "import_handler_id is required"

    return BaseImportHandlerItem
])

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

      $uploadPredict: (server) =>
        url = "#{@BASE_API_URL}#{@id}/action/upload_to_server/"
        @$make_request(url, {}, "PUT", {'server': server})

    return XmlImportHandler
])

.factory('Field', [
  'settings'
  'BaseModel'
  
  (settings, BaseModel) ->
    class Field extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/fields/"
      API_FIELDNAME: 'xml_field'
      @LIST_MODEL_NAME: 'fields'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name'

      TYPES_LIST: ['integer', 'boolean', 'string', 'float', 'json']
      TRANSFORM_LIST: ['csv', 'json']

      id: null

      @$get_api_url: (opts, model) ->
        if model?
          handler_id = model.import_handler_id
        else
          handler_id = opts.import_handler_id

        if model?
          entity_id = model.entity_id
        else
          entity_id = opts.entity_id

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/fields/"

      @$beforeLoadAll: (opts) ->
        if not opts.import_handler_id
          throw new Error "import_handler_id is required"

        if not opts.entity_id
          throw new Error "entity_id is required"

    return Field
])

.factory('Sqoop', [
  'settings'
  'BaseModel'

  (settings, BaseModel) ->
    class Sqoop extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/sqoop_imports/"
      API_FIELDNAME: 'sqoop_import'
      @LIST_MODEL_NAME: 'sqoop_imports'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,text,target,table,where,direct,mappers,datasource,\
datasource_id,entity_id'

      id: null

      @$get_api_url: (opts, model) ->
        if model?
          handler_id = model.import_handler_id
        else
          handler_id = opts.import_handler_id

        if model?
          entity_id = model.entity_id
        else
          entity_id = opts.entity_id

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/sqoop_imports/"

      @$beforeLoadAll: (opts) ->
        if not opts.import_handler_id
          throw new Error "import_handler_id is required"

        if not opts.entity_id
          throw new Error "entity_id is required"

      saveText: () =>
        if not @text
          @edit_err = 'Please enter a text'
          return
        @loading_state = true
        self = @
        @$save({only: ['text']}).then((opts) ->
          self.loading_state = false
          self.msg = 'Sqoop item has been saved'
          self.edit_err = null
          self.err = null
        )

    return Sqoop
])

.factory('XmlQuery', [
  'settings'
  'BaseModel'

  (settings, BaseModel) ->
    class Query extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/queries/"
      API_FIELDNAME: 'query'
      @MAIN_FIELDS: 'id,text,target'

      id: null
      text: null
      target: null

      loadFromJSON: (origData) =>
        super origData

        if not @target?
          @target = undefined

        if not @text
          @err = 'Please enter the query text'

      @$get_api_url: (opts, model) ->
        if model?
          handler_id = model.import_handler_id
        else
          handler_id = opts.import_handler_id

        if model?
          entity_id = model.entity_id
        else
          entity_id = opts.entity_id

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/queries/"

      @$beforeLoadAll: (opts) ->
        if not opts.import_handler_id
          throw new Error "import_handler_id is required"

        if not opts.entity_id
          throw new Error "entity_id is required"

      getParams: () ->
        expr = /%\((\w+)\)s/gi
        params = []
        matches = expr.exec(@text)
        while matches
          params.push matches[1]
          matches = expr.exec(@text)
        return params

      $run: (limit, params, datasource, handlerUrl) ->
        data = {
          sql: @text,
          params: JSON.stringify(params),
          limit: limit,
          datasource: datasource
        }
        @$make_request("#{handlerUrl}/action/run_sql/", {}, "PUT", data)

    return Query
])

.factory('Entity', [
  'settings'
  'BaseImportHandlerItem'
  'Field'
  'XmlQuery'
  'Sqoop'

  (settings, BaseImportHandlerItem, Field, Query, Sqoop) ->
    class Entity extends BaseImportHandlerItem
      API_FIELDNAME: 'entity'
      @LIST_MODEL_NAME: 'entities'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name'
      @ITEM_NAME: 'entities'

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

          if origData.query_obj?
            @query_obj = new Query(_.extend origData.query_obj, defaults)
            @query_id = @query_id || @query_obj.id

          if origData.sqoop_imports?
            @sqoop_imports = []
            for data in origData.sqoop_imports
              @sqoop_imports.push new Sqoop(_.extend data, defaults)

    return Entity
])

.factory('InputParameter', [
  'settings'
  'BaseImportHandlerItem'
  
  (settings, BaseImportHandlerItem) ->
    class InputParameter extends BaseImportHandlerItem
      API_FIELDNAME: 'xml_input_parameter'
      @ITEM_NAME: 'input_parameters'
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

.factory('Datasource', [
  'settings'
  'BaseImportHandlerItem'

  (settings, BaseImportHandlerItem) ->
    class Datasource extends BaseImportHandlerItem
      API_FIELDNAME: 'xml_data_source'
      @LIST_MODEL_NAME: 'datasources'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @ITEM_NAME: 'datasources'
      @MAIN_FIELDS: 'id,name,type,params'

      id: null
      name: null
      type: null
      params: {}

    return Datasource
])

.factory('Script', [
  'settings'
  'BaseImportHandlerItem'

  (settings, BaseImportHandlerItem) ->
    class Script extends BaseImportHandlerItem
      API_FIELDNAME: 'xml_script'
      @LIST_MODEL_NAME: 'xml_scripts'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,import_handler_id,data'
      @ITEM_NAME: 'scripts'

      id: null
      import_handler_id: null
      data: null

    return Script
])
