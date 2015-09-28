angular.module('app.servers.model', ['app.config'])

.factory('ServerFile', [
  'BaseModel'
  'settings'
  
  (BaseModel, settings) ->
    class ServerFile extends BaseModel
      API_FIELDNAME: 'server_file'

      id: null  # guid
      server_id: null

      # Object (import handler or model) details
      object_id: null
      object_type: null
      object_name: null
      obj: null

      name: null
      size: null
      updated: null

      $reload: () ->
        base_url = @constructor.$get_api_url({}, @)
        return @$make_request("#{base_url}#{@id}/action/reload/", {}, 'PUT')

    return ServerFile
])

.factory('ModelFile', [
  'ServerFile'
  'Model'
  'settings'
  
  (ServerFile, Model, settings) ->
    class ModelFile extends ServerFile
      @LIST_MODEL_NAME: 'model_files'
      LIST_MODEL_NAME: @LIST_MODEL_NAME

      @$get_api_url: (opts, model) ->
        server_id = opts.server_id || model.server_id
        if not server_id then throw new Error 'server_id is required'
        return "#{settings.apiUrl}servers/#{server_id}/files/models/"

      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.object_id?
            @obj = new Model({
              id: origData.object_id
              name: origData.object_name
            })
          console.log origData

    return ModelFile
])

.factory('ImportHandlerFile', [
  'ServerFile'
  'XmlImportHandler'
  'settings'
  
  (ServerFile, XmlImportHandler, settings) ->
    class ImportHandlerFile extends ServerFile
      @LIST_MODEL_NAME: 'importhandlers_files'
      LIST_MODEL_NAME: @LIST_MODEL_NAME

      @$get_api_url: (opts, model) ->
        server_id = opts.server_id || model.server_id
        if not server_id then throw new Error 'server_id is required'
        return "#{settings.apiUrl}servers/#{server_id}/files/importhandlers/"

      $generateS3Url: () =>
        base_url = @constructor.$get_api_url({}, @)
        @$make_request("#{base_url}#{@id}/action/generate_url/",
                       {}, 'GET', {})

      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.object_id?
            if origData.object_type == 'xml'
              @obj = new XmlImportHandler({
                id: origData.object_id
                name: origData.object_name
              })
            else
              throw new Error "unsuported import handler type"

    return ImportHandlerFile
])

.factory('Server', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Server extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}servers/"
      BASE_UI_URL: '/servers'
      API_FIELDNAME: 'server'
      @MAIN_FIELDS: 'id,name,ip'

      id: null
      name: null
      ip: null

      # This info could be loaded usign `getFiles` method
      models_list: null
      importhandlers_list: null

    return Server
])
