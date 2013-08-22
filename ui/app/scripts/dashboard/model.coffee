angular.module('app.dashboard.model', ['app.config'])

.factory('Statistics', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Model'
  'ImportHandler'

  ($http, $q, settings, BaseModel, Model, ImportHandler) ->

    class Statistics extends BaseModel
      API_FIELDNAME: 'statistics'
      BASE_API_URL: "#{settings.apiUrl}statistics"

      $load: (opts) ->
        @$make_request("#{@BASE_API_URL}/", opts)

      getModelUrl: (_id) =>
        model = new Model({'_id': _id})
        return model.objectUrl()

      getImportHandlerUrl: (_id) =>
        model = new ImportHandler({'_id': _id})
        return model.objectUrl()

    return Statistics
])