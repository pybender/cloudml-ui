angular.module('app.servers.model', ['app.config'])


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

      getUrl: =>
        return "#{@BASE_API_URL}#{@id || ''}/"

      $getFiles: (folder) ->
        url = "#{@BASE_API_URL}#{@id}/action/list/?folder=#{folder}"
        return @$make_request(url, {}, 'GET', data={}, load=false)

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
