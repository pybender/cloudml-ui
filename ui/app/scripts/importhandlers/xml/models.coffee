angular.module('app.importhandlers.xml.models', ['app.config'])

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

        if not handler_id
          throw new Error "import_handler_id:#{handler_id} should be defined"

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/#{@ITEM_NAME}/"

      @$beforeLoadAll: (opts) ->
        if opts?
          if opts.import_handler_id?
            return {import_handler_id: opts.import_handler_id}
        throw new Error "import_handler_id is required"

    return BaseImportHandlerItem
])

.factory('XmlImportHandler', [
  'settings'
  'BaseModel'
  'InputParameter'
  'Entity'
  'PredictModel'
  'Script'
  'Datasource'
  'Field'
  
  (settings, BaseModel, InputParameter, Entity, PredictModel, Script, Datasource, Field) ->
    class XmlImportHandler extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/"
      BASE_UI_URL: "/importhandlers/xml"
      API_FIELDNAME: 'xml_import_handler'
      @LIST_MODEL_NAME: 'xml_import_handlers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: ['id','name','created_on','created_by', 'updated_on',
                     'updated_by','import_params'].join(',')
      TYPE: 'XML'

      id: null
      name: null
      created_on: null
      created_by: null

      xml_input_parameters: []
      xml_scripts: []
      xml_data_sources: []
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

          if origData.xml_scripts?
            @xml_scripts = []
            for paramData in origData.xml_scripts
              @xml_scripts.push new Script(_.extend paramData, defaults)

          if origData.xml_data_sources?
            @xml_data_sources = []
            for paramData in origData.xml_data_sources
              @xml_data_sources.push new Datasource(_.extend paramData, defaults)

          if origData.predict?
            @predict.models = (new PredictModel(_.extend mod, defaults) \
              for mod in origData.predict.models)

      $uploadPredict: (server) =>
        url = "#{@BASE_API_URL}#{@id}/action/upload_to_server/"
        @$make_request(url, {}, "PUT", {'server': server})

      $clone: (opts={}) ->
        @$make_request("#{@BASE_API_URL}#{@id}/action/clone/", {}, "POST", {})

      $listFields: ->
        resolver = Field.$buildLoadAllResolver()
        Field.$make_all_request("#{@BASE_API_URL}#{@id}/action/list_fields/", resolver)

      @$loadAllWithoutPaging: ->
        url = @$get_api_url({}) + 'action/brief/'
        resolver = (resp) -> { objects: resp.data['xml_import_handlers'] }
        @$make_all_request(url, resolver, {})

      $updateXml: ->
        @$make_request("#{@BASE_API_URL}#{@id}/action/update_xml/", {}, 'PUT',
          {'data': @xml})

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

        if not entity_id or not handler_id
          throw new Error "entity_id:#{entity_id}, import_handler_id:#{handler_id} both should be defined"

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/fields/"

      @$beforeLoadAll: (opts) ->
        if not opts.entity_id or not opts.import_handler_id
          throw new Error "entity_id:#{opts.entity_id}, import_handler_id:#{opts.import_handler_id} both should be defined"

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
      @MAIN_FIELDS: ['id','text','target','table','where','direct','mappers',
                     'datasource','datasource_id','entity_id', 'options'].join(',')

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

        if not entity_id or not handler_id
          throw new Error "entity_id:#{entity_id}, import_handler_id:#{handler_id} both should be defined"

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/sqoop_imports/"

      @$beforeLoadAll: (opts) ->
        if not opts.entity_id or not opts.import_handler_id
          throw new Error "entity_id:#{opts.entity_id}, import_handler_id:#{opts.import_handler_id} both should be defined"

      pigFields: (opts) =>
        base_url = @constructor.$get_api_url({}, @)
        url = "#{base_url}#{@id}/action/pig_fields/"
        @$make_request(url, {}, "GET", {})

      getPigFields: (opts) =>
        data = {
          params: JSON.stringify(opts.params),
        }
        base_url = @constructor.$get_api_url({}, @)
        url = "#{base_url}#{@id}/action/pig_fields/"
        @$make_request(url, {}, "PUT", data)

      getParams: ->
        # TODO: use method from BaseQueryModel
        params = []
        regex = new RegExp('#{(\\w+)}', 'gi')
        matches = regex.exec(@text)
        while matches
          if matches[1] not in params
            params.push matches[1]
          matches = regex.exec(@text)
        return params

      saveText: () =>
        if not @text
          @edit_err = 'Please enter a text'
          return
        @loading_state = true
        self = @
        @$save {only: ['text']}
        .then (opts) ->
          self.loading_state = false
          self.msg = 'Sqoop item has been saved'
          self.edit_err = null
          self.err = null
        , (opts) ->
          self.loading_state = false
          self.msg = 'http error saving Sqoop item'
          self.edit_err = 'http error saving Sqoop item'
          self.err = 'http save error'

    return Sqoop
])


.factory('XmlQuery', [
  'settings'
  'BaseQueryModel'

  (settings, BaseQueryModel) ->
    class Query extends BaseQueryModel
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

        if not entity_id or not handler_id
          throw new Error "entity_id:#{entity_id}, import_handler_id:#{handler_id} both should be defined"

        return "#{settings.apiUrl}xml_import_handlers/\
#{handler_id}/entities/#{entity_id}/queries/"

      @$beforeLoadAll: (opts) ->
        if not opts.entity_id or not opts.import_handler_id
          throw new Error "entity_id:#{opts.entity_id}, import_handler_id:#{opts.import_handler_id} both should be defined"

      getParams: ->
        @_getParams BaseQueryModel.PARAMS_HASH_REGEX, @text

      $run: (limit, params, datasource, handlerUrl) ->
        @_runSql @text, params, datasource, limit,
          "#{handlerUrl}/action/run_sql/"

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
              sqoop = new Sqoop(_.extend data, defaults)
              sqoop.pigFields().then((resp) ->
                sqoop.pig_fields = resp.data.pig_fields
              , ((opts) ->
                sqoop.pig_fields_err = opts.data.response?.error?.message || 'error'
              ))
              @sqoop_imports.push sqoop

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
      @MAIN_FIELDS: 'id,import_handler_id,data,type'
      @ITEM_NAME: 'scripts'
      TYPES_LIST: ['python_code', 'python_file']
      DEFAULT_FIELDS_TO_SAVE: ['import_handler_id', 'data', 'data_file', 'data_url', 'type']

      id: null
      import_handler_id: null
      data: null
      type: null
      data_file: null
      data_url: null

      $getScriptString: ->
        base_url = @constructor.$get_api_url({}, @)
        @$make_request("#{base_url}#{@id}/action/script_string/", {}, 'GET')

      $save: (opts={}) ->
        if 'type' in opts.only
          if @type == 'python_file'
            if 'data' in opts.only
              _.remove opts.only, (x)-> x is 'data'
          else if @type == 'python_code'
            if 'data_file' in opts.only
              _.remove opts.only, (x)-> x is 'data_file'
            if 'data_url' in opts.only
              _.remove opts.only, (x)-> x is 'data_url'
        super opts

    return Script
])

# predict models

.factory('PredictModelWeight', [
  'settings'
  'BaseImportHandlerItem'

  (settings, BaseImportHandlerItem) ->
    class PredictModelWeight extends BaseImportHandlerItem
      API_FIELDNAME: 'predict_model_weight'
      @LIST_MODEL_NAME: 'predict_model_weights'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @ITEM_NAME: 'predict_model_weights'
      @MAIN_FIELDS: 'id,label,value,script'

      constructor: (opts) ->
        super opts
        @BASE_API_URL = PredictModelWeight.$get_api_url({
          predict_model_id: @predict_model_id
          import_handler_id: @import_handler_id
        }, @)

      @$get_api_url: (opts, self) ->
        if self?
          model_id = self.predict_model_id
          import_handler_id = self.import_handler_id
        else
          model_id = opts.predict_model_id
          import_handler_id = opts.import_handler_id
        if not model_id then throw new Error 'predict_model_id is required'
        if not import_handler_id then throw new Error 'import_handler_id is required'
        return "#{settings.apiUrl}xml_import_handlers/#{import_handler_id}/predict_models/\
#{model_id}/weights/"

      id: null
      label: null
      value: null
      script: null

    return PredictModelWeight
])

.factory('PredictModel', [
  'settings'
  'BaseImportHandlerItem'
  'PredictModelWeight'

  (settings, BaseImportHandlerItem, PredictModelWeight) ->
    class PredictModel extends BaseImportHandlerItem
      API_FIELDNAME: 'predict_model'
      @LIST_MODEL_NAME: 'predict_models'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @ITEM_NAME: 'predict_models'
      @MAIN_FIELDS: 'id,name,value,script'

      id: null
      name: null
      value: null
      script: null

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          defaults= {
            predict_model_id: @id
            predict_model: @
            import_handler_id: @import_handler_id
          }
          if origData.predict_model_weights?
            @predict_model_weights = []
            for data in origData.predict_model_weights
              @predict_model_weights.push new PredictModelWeight(_.extend data, defaults)


    return PredictModel
])

.factory('PredictLabel', [
  'settings'
  'BaseImportHandlerItem'
  'PredictModel'

  (settings, BaseImportHandlerItem, PredictModel) ->
    class PredictLabel extends BaseImportHandlerItem
      API_FIELDNAME: 'predict_label'
      @LIST_MODEL_NAME: 'predict_labels'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @ITEM_NAME: 'predict_labels'
      @MAIN_FIELDS: 'id,predict_model,script'

      id: null
      predict_model: null
      script: null

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          defaults= {
            result_label_id: @id
            result_label: @
            import_handler_id: @import_handler_id
          }
          if origData.predict_model?
            @predict_model = new PredictModel(_.extend origData.predict_model, defaults)


    return PredictLabel
])


.factory('PredictProbability', [
  'settings'
  'BaseImportHandlerItem'
  'PredictModel'

  (settings, BaseImportHandlerItem, PredictModel) ->
    class PredictProbability extends BaseImportHandlerItem
      API_FIELDNAME: 'predict_probability'
      @LIST_MODEL_NAME: 'predict_probabilities'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @ITEM_NAME: 'predict_probabilities'
      @MAIN_FIELDS: 'id,predict_model,script, label'

      id: null
      predict_model: null
      label: null
      script: null

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          defaults= {
            result_probability_id: @id
            result_probability: @
            import_handler_id: @import_handler_id
          }
          if origData.predict_model?
            @predict_model = new PredictModel(_.extend origData.predict_model, defaults)


    return PredictProbability
])
