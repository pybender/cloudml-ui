angular.module('app.servers.model', ['app.config'])


.factory('ModelFile', [
  'BaseModel'
  'Model'
  'settings'
  
  (BaseModel, Model, settings) ->
    class ModelFile extends BaseModel
      API_FIELDNAME: 'server_file'

      server_id: null

      # Model details
      id: null
      obj: null
      object_name: null

      # Metadata from amazon
      name: null
      size: null
      updated: null

      @$get_api_url: (opts, model) ->
        server_id = opts.server_id || model.server_id
        if not server_id then throw new Error 'server_id is required'
        return "#{settings.apiUrl}servers/#{server_id}/files/"

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
  'BaseModel'
  'ImportHandler'
  
  (BaseModel, ImportHandler) ->
    class ImportHandlerFile extends BaseModel
      # Import Handler details
      object_id: null
      type: null
      object_name: null
      obj: null

      name: null
      size: null
      updated: null

      @$get_api_url: (opts, model) ->
        server_id = opts.server_id || model.server_id
        if not server_id then throw new Error 'server_id is required'
        return "#{settings.apiUrl}servers/#{server_id}/files/"

      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.object_id?
            @obj = new ImportHandler({
              id: origData.object_id
              name: origData.object_name
              type: origData.type
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
      BASE_UI_URL: '/servers/'
      API_FIELDNAME: 'server'
      @MAIN_FIELDS: 'id,name,ip'

      id: null
      name: null
      ip: null

      # This info could be loaded usign `getFiles` method
      models_list: null
      importhandlers_list: null

      getUrl: =>
        return "#{@BASE_API_URL}#{@id || ''}/"

      $getFiles: (folder) ->
        url = "#{@BASE_API_URL}#{@id}/action/list/?folder=#{folder}"
        return @$make_request(url, {}, 'GET')

      $removeFile: (fileName) ->
        url = "#{@BASE_API_URL}#{@id}/action/remove/"
        return @$make_request(url, {}, 'PUT',
          data={filename: fileName}, load=false)

      $updateFileAtServer: (fileName) ->
        url = "#{@BASE_API_URL}#{@id}/action/update_at_server/"
        return @$make_request(url, {}, 'PUT',
          data={filename: fileName}, load=false)

    return Server
])
