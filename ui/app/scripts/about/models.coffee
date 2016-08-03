angular.module('app.about.model', ['app.config'])

.factory('About', [
  '$http'
  '$q'
  'settings'
  'BaseModel'

  ($http, $q, settings, BaseModel) ->

    class About extends BaseModel
      API_FIELDNAME: 'about'
      BASE_API_URL: "#{settings.apiUrl}about"

      $load: (opts) ->
        @$make_request("#{@BASE_API_URL}/", opts)

    return About
])