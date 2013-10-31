angular.module('app.models.model', ['app.config'])

.factory('Model', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'ImportHandler'
  'DataSet'
  'FeaturesSet'
  'Classifier'
  
  ($http, $q, settings, BaseModel, ImportHandler, DataSet,
    FeaturesSet, Classifier) ->
    ###
    Model
    ###
    class Model extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}models/"
      BASE_UI_URL: '/models/'
      API_FIELDNAME: 'model'
      DEFAULT_FIELDS_TO_SAVE: ['train_import_handler', 'features',
                               'trainer', 'test_import_handler', 'name',
                               'test_import_handler_file',
                               'train_import_handler_file']
      @MAIN_FIELDS: 'name,_id,status'

      _id: null
      name: null
      status: null
      created_on: null
      updated_on: null
      tags: []

      trainer: null
      importParams: null
      features: null
      featuresSet: null
      features_set_id: null

      train_import_handler: null
      test_import_handler: null
      datasets: []

      loadFromJSON: (origData) =>
        super origData

        if origData?
          # TODO:
          @features = angular.toJson(
            angular.fromJson(origData['features']), pretty=true)
          if origData.test_import_handler?
            @test_import_handler_obj = new ImportHandler(
              origData['test_import_handler'])
            @test_import_handler = @test_import_handler_obj._id
          if origData.train_import_handler?
            @train_import_handler_obj = new ImportHandler(
              origData['train_import_handler'])
            @train_import_handler = @train_import_handler_obj._id
          if origData.datasets?
            @datasets_obj = for row in origData['datasets']
              new DataSet(row)
          if origData.features_set_id?
            @featuresSet = new FeaturesSet({'_id': @features_set_id})
          if origData.classifier?
            @classifier = new Classifier(
              _.extend origData.classifier, {'model_id': @_id})

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

      $cancel_request_spot_instance: =>
        url = "#{@BASE_API_URL}#{@_id}/action/cancel_request_instance/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.model.status)

    return Model
])


.factory('Tag', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Tag extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}tags/"
      API_FIELDNAME: 'tag'

      _id: null
      id: null
      text: null

    return Tag
])