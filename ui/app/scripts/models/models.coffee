angular.module('app.models.model', ['app.config'])

.factory('Model', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'ImportHandler'
  'XmlImportHandler'
  'DataSet'
  'FeaturesSet'
  'Classifier'
  
  ($http, $q, settings, BaseModel, ImportHandler, XmlImportHandler,
    DataSet, FeaturesSet, Classifier) ->
    ###
    Model
    ###
    class Model extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}models/"
      BASE_UI_URL: '/models'
      API_FIELDNAME: 'model'
      DEFAULT_FIELDS_TO_SAVE: ['train_import_handler', 'features',
                               'trainer', 'test_import_handler', 'name',
                               'test_import_handler_file',
                               'train_import_handler_file']
      @MAIN_FIELDS: 'name,id,status'
      @LIST_MODEL_NAME: 'models'
      LIST_MODEL_NAME: @LIST_MODEL_NAME

      id: null
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
      sorted_data_fields: null
      labels: null

      trainer_s3_url: null

      loadFromJSON: (origData) ->
        super origData

        if origData?
          # TODO:
          if origData.features?
            @features = angular.toJson(
              angular.fromJson(origData['features']), pretty=true)

          if origData.test_import_handler?
            if origData.test_import_handler_type == 'xml'
              cls = XmlImportHandler
            else
              cls = ImportHandler
            @test_import_handler_obj = new cls(
              origData['test_import_handler'])
            @test_import_handler = @test_import_handler_obj.id

          if origData.train_import_handler?
            if origData.train_import_handler_type == 'xml'
              cls = XmlImportHandler
            else if origData.train_import_handler_type == 'json'
              cls = ImportHandler
            else
              throw new Error('Need to load import handler type')
            @train_import_handler_obj = new cls(
              origData['train_import_handler'])
            @train_import_handler = @train_import_handler_obj.id

          if origData.datasets?
            @datasets_obj = for row in origData['datasets']
              new DataSet(row)
          if origData.features_set_id?
            @featuresSet = new FeaturesSet({'id': @features_set_id})
          if origData.classifier?
            @classifier = new Classifier(
              _.extend origData.classifier, {'model_id': @id})
          if origData.tags?
            @tags = for tag in origData['tags']
              tag['text']
          if origData.data_fields?
            @sorted_data_fields = _.sortBy origData['data_fields'], (s)-> s

      downloadFeaturesUrl: ->
        return "#{@BASE_API_URL}#{@id}/action/features_download/?"

      @$by_handler: (opts) ->
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

      $train: (opts={}) ->
        data = {}
        for key, val of opts
          if key == 'parameters' then val = JSON.stringify(val)
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@id}/action/train/", {}, "PUT", data)

      $classifierGridSearch: (opts={}) ->
        data = {}
        for key, val of opts
          if key == 'parameters' then val = JSON.stringify(val)
          data[key] = val
        @$make_request(
          "#{@BASE_API_URL}#{@id}/action/grid_search/", {}, "PUT", data)

      $cancel_request_spot_instance: ->
        url = "#{@BASE_API_URL}#{@id}/action/cancel_request_instance/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) ->
            @status = resp.data.model.status)

      $uploadPredict: (server) ->
        url = "#{@BASE_API_URL}#{@id}/action/upload_to_server/"
        @$make_request(url, {}, "PUT", {'server': server})

      $getTrainS3Url: ()->
        url = "#{@BASE_API_URL}#{@id}/action/trainer_download_s3url/"
        @$make_request(url, {}, "GET", {})

      $getDataSetDownloads: ()->
        url = "#{@BASE_API_URL}#{@id}/action/dataset_download/"
        @$make_request(url, {}, "GET", {})

      $putDataSetDownload: (datasetId)->
        url = "#{@BASE_API_URL}#{@id}/action/dataset_download/"
        @$make_request(url, {}, "PUT", {dataset: datasetId})

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

      id: null
      text: null

    return Tag
])