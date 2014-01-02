angular.module('app.logmessages.model', ['app.config'])

.factory('LogMessage', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class LogMessage  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}logs/"
      API_FIELDNAME: 'log'

      id: null
      level: null
      type: null
      content: null
      params: {}

    return LogMessage
])