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

      @$active_models: (opts) ->
        resolver = (resp, Model) ->
          {
            total: resp.data.found
            objects: resp.data.files
            _resp: resp
          }
        @$make_all_request("#{@prototype.BASE_API_URL}action/models/",
                           resolver, opts)

    return Server
])


.factory('ModelVerification', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Model'
  'Server'
  'TestResult'
  
  ($http, $q, settings, BaseModel, Model, Server, TestResult) ->
    class ModelVerification extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}servers/verifications/"
      BASE_UI_URL: '/servers/verifications'
      API_FIELDNAME: 'server_model_verification'
      @MAIN_FIELDS: 'id,model,server,test_result,created_by,created_on,import_handler'

      id: null
      server: null
      model: null
      data: null

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          if origData.model?
            @model_obj = new Model(_.extend origData.model)
          if origData.test_result?
            @test_result_obj = new TestResult(_.extend origData.test_result)
          if origData.server?
            @server_obj = new Server(_.extend origData.server)

      $save: (opts={}) =>
        data = {}
        for name in opts.only
          val = eval("this." + name)
          if val? then data[name] = val
        data['description'] = JSON.stringify(@description)
        method = if @isNew() then "POST" else "PUT"
        base_url = @constructor.$get_api_url(opts, @)
        url = if @id? then base_url + @id + "/" else base_url
        @$make_request(url, {}, method, data)

      $verify: (opts) ->
        @$make_request(
          "#{@BASE_API_URL}#{@id}/action/verify/", {},
          "PUT", opts)

    return ModelVerification
])
