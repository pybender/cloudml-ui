angular.module('app.importhandlers.model', ['app.config'])

.factory('ImportHandler', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Import Handler
    ###
    class ImportHandler  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}importhandlers/"
      BASE_UI_URL: '/importhandlers/'
      API_FIELDNAME: 'import_handler'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'type', 'data']

      _id: null
      created_on: null
      updated_on: null
      name: null
      type: null
      data: null
      import_params: []

      loadFromJSON: (origData) =>
        super origData
        if origData?
          @data = angular.toJson(origData['data'], pretty=true)

      $save: (opts={}) =>
        @type = @type['name']
        super opts

      $loadData: (opts={}) =>
        # Executes loading dataset task
        data = {}
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@_id}/action/load/", {}, "PUT", data)

    return ImportHandler
])