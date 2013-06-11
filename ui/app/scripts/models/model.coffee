angular.module('app.models.model', ['app.config'])

.factory('Model', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'ImportHandler'
  
  ($http, $q, settings, BaseModel, ImportHandler) ->
    ###
    Model
    ###
    class Model extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}models/"
      BASE_UI_URL: '/models/'
      API_FIELDNAME: 'model'
      DEFAULT_FIELDS_TO_SAVE: ['train_import_handler', 'features',
                               'trainer', 'test_import_handler', 'name']
      @MAIN_FIELDS: 'name,_id,status,train_import_handler._id,
train_import_handler.import_params,train_import_handler.name,
test_import_handler._id,test_import_handler.import_params,
test_import_handler.name'


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
          @features = angular.toJson(origData['features'], pretty=true)
          if origData.test_import_handler?
            @test_import_handler_obj = new ImportHandler(
              origData['test_import_handler'])
            @test_import_handler = @test_import_handler_obj._id
          if origData.train_import_handler?
            @train_import_handler_obj = new ImportHandler(
              origData['train_import_handler'])
            @train_import_handler = @train_import_handler_obj._id

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

      $reload: =>
        @$make_request("#{@BASE_API_URL}#{@_id}/action/reload/", {}, "GET", {})

      @$by_handler: (opts) =>
        resolver = (resp, Model) ->
          {
            total: resp.data.found
            objects: (
              new Model(_.extend(obj, {loaded: true})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request("#{@prototype.BASE_API_URL}action/by_importhandler/",
                           resolver, opts)

      $train: (opts={}) =>
        data = {}
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@_id}/action/train/", {}, "PUT", data)

    return Model
])