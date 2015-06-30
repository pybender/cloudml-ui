angular.module('app.dashboard.model', ['app.config'])

.factory('Statistics', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Model'
  'XmlImportHandler'

  ($http, $q, settings, BaseModel, Model, ImportHandler) ->

    class Statistics extends BaseModel
      API_FIELDNAME: 'statistics'
      BASE_API_URL: "#{settings.apiUrl}statistics"

      $load: (opts) ->
        @$make_request("#{@BASE_API_URL}/", opts)

      getModelUrl: (id) ->
        model = new Model({'id': id})
        return model.objectUrl()

      getImportHandlerUrl: (id) ->
        model = new ImportHandler({'id': id})
        return model.objectUrl()

    return Statistics
])