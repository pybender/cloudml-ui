angular.module('app.testresults.model', ['app.config'])

.factory('TestResult', [
  '$http'
  '$q'
  'settings'
  'Model'
  'BaseModel'
  
  ($http, $q, settings, Model, BaseModel) ->
    ###
    Trained Model Test
    ###
    class TestResult extends BaseModel
      API_FIELDNAME: 'test'
      @MAIN_FIELDS: 'name,status'
      DEFAULT_FIELDS_TO_SAVE: ['importhandler', 'train_importhandler',
                                'features', 'trainer', 'name']

      _id: null
      accuracy: null
      created_on: null
      data_count: null
      name: null
      parameters: null
      model: null
      model_name: null
      loaded: false

      constructor: (opts) ->
        super opts
        @BASE_API_URL = TestResult.$get_api_url(@model_id)
        @BASE_UI_URL = "/models/#{@model_id}/tests/"

      @$get_api_url: (model_id) ->
        return "#{settings.apiUrl}models/#{model_id}/tests/"

      examplesUrl: =>
        return "#{@BASE_UI_URL}#{@_id}?action=examples:list"

      avaragePrecisionUrl: =>
        return "#{@BASE_UI_URL}#{@_id}/grouped_examples"

      fullName: =>
        if @model? || @model_name
          return (@model_name || @model.name) + " / " + @name
        return @name

      loadFromJSON: (origData) =>
        super origData
        if 'model' in origData
          @model = new Model(origData['model'])
          @model_name = origData['model']['name']

      $run: (data) =>
        if @_id?
          throw new Error "You can run only new test"

        @$make_request(@BASE_API_URL, {}, 'POST', data)

      @$loadAll: (model_id, opts) ->
        if not model_id
          throw new Error "Model is required to load tests"

        resolver = (resp, Model) ->
          {
            objects: (
              new Model(_.extend(obj, {loaded: true, model_id: model_id})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(TestResult.$get_api_url(model_id), resolver, opts)

    return TestResult
])