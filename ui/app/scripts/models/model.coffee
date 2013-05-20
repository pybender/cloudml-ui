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
      DEFAULT_FIELDS_TO_SAVE: ['importhandler', 'train_importhandler',
                                'features', 'trainer', 'name']

      _id: null
      name: null
      status: null
      created_on: null
      updated_on: null

      trainer: null
      importParams: null
      importhandler: null
      train_importhandler: null
      features: null

      loadFromJSON: (origData) =>
        super origData

        if origData?
          @created_on = String(origData['created_on'])
          #if 'features' in origData
          @features = angular.toJson(origData['features'], pretty=true)
          #if 'importhandler' in origData
          @importhandler = angular.toJson(origData['importhandler'],
                                        pretty=true)
          #if 'train_importhandler' in origData
          @train_importhandler = angular.toJson(
              origData['train_importhandler'], pretty=true)

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

      $train: (opts={}) =>
        data = {}
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@_id}/action/train/", {}, "PUT", data)

    return Model
])