angular.module('app.models.model', ['app.config'])

.factory('Model', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Model
    ###
    class Model extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}models/"
      BASE_UI_URL: '/models/'
      API_FIELDNAME: 'model'
      DEFAULT_FIELDS_TO_SAVE: ['train_import_handler', 'features',
                               'trainer', 'test_import_handler', 'name']

      _id: null
      name: null
      status: null
      created_on: null
      updated_on: null

      trainer: null
      importParams: null
      features: null

      train_import_handler: null
      test_import_handler: null

      loadFromJSON: (origData) =>
        super origData

        if origData?
          @created_on = String(origData['created_on'])
          @features = angular.toJson(origData['features'], pretty=true)

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

      $reload: =>
        @$make_request("#{@BASE_API_URL}#{@_id}/action/reload/", {}, "GET", {})

      $train: (opts={}) =>
        data = {}
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@_id}/action/train/", {}, "PUT", data)

    return Model
])