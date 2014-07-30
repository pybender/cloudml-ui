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
      object_id: null

      @$loadAll: (opts) ->
        resolver = (resp, Model) ->
          {
            next_token: resp.data.next_token,
            objects: (
              new Model(_.extend(obj, {loaded: true})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request("#{@prototype.BASE_API_URL}", resolver, opts)

    return LogMessage
])