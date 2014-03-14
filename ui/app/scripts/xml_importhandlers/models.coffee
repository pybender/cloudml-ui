angular.module('app.xml_importhandlers.models', ['app.config'])


.factory('XmlImportHandler', [
  'settings'
  'BaseModel'
  'InputParameter'
  
  (settings, BaseModel, InputParameter) ->
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
          if origData.xml_input_parameters?
            defaultData = {'import_handler_id': @id}
            @xml_input_parameters = []
            for paramData in origData.xml_input_parameters
              @xml_input_parameters.push new InputParameter(
                _.extend paramData, defaultData)
          
    return XmlImportHandler
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

.factory('Datasource', [
  'settings'
  'BaseModel'

  (settings, BaseModel) ->
    class Datasource extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}xml_import_handlers/datasources/"
      API_FIELDNAME: 'xml_datasource'
      @LIST_MODEL_NAME: 'datasources'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,params'

      id: null
      name: null
      type: null
      params: {}

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)

    return Datasource
])
