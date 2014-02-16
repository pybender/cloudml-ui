angular.module('app.testresults.model', ['app.config'])

.factory('TestResult', [
  '$http'
  '$q'
  'settings'
  'Model'
  'BaseModel'
  'DataSet'
  
  ($http, $q, settings, Model, BaseModel, DataSet) ->
    ###
    Trained Model Test
    ###
    class TestResult extends BaseModel
      API_FIELDNAME: 'test'
      @MAIN_FIELDS: 'name,status,created_on,created_by'
      DEFAULT_FIELDS_TO_SAVE: ['importhandler', 'train_importhandler',
                                'features', 'trainer', 'name']

      id: null
      accuracy: null
      created_on: null
      data_count: null
      name: null
      parameters: null
      model: null
      model_name: null
      confusion_matrix_calculations: null
      loaded: false

      constructor: (opts) ->
        super opts
        @BASE_API_URL = TestResult.$get_api_url(@model_id)
        @BASE_UI_URL = "/models/#{@model_id}/tests/"

      @$get_api_url: (model_id) ->
        return "#{settings.apiUrl}models/#{model_id}/tests/"

      objectUrl: =>
        return @BASE_UI_URL + @id

      examplesUrl: =>
        return "#{@BASE_UI_URL}#{@id}?action=examples:list"

      examplesCsvUrl: () ->
        return "#{@BASE_API_URL}#{@id}/examples/action/csv/"

      avaragePrecisionUrl: =>
        return "#{@BASE_UI_URL}#{@id}/grouped_examples"

      fullName: =>
        if @model? || @model_name
          return (@model_name || @model.name) + " / " + @name
        return @name

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if 'model' in origData
            @model = new Model(origData['model'])
            @model_name = origData['model']['name']

          if origData.dataset?
            @dataset_obj = new DataSet(origData['dataset'])
            @dataset = @dataset.id

      $run: (opts) =>
        if @id?
          throw new Error "You can run only new test"

        data = {}
        for key, val of opts
          if key == 'parameters' then val = JSON.stringify(val)
          data[key] = val

        @$make_request(@BASE_API_URL, {}, 'POST', data)

      @$loadAll: (opts) ->
        model_id = opts.model_id
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

      $get_confusion_matrix: (weight0, weight1) ->
        url = "#{@BASE_API_URL}#{@id}/action/confusion_matrix/"
        data = {weight0: weight0, weight1: weight1}
        @$make_request(url, data, "GET", {})

      @$get_examples_size: (opts) ->
        url = TestResult.$get_api_url() + "action/examples_size/"

        resolver = (resp, Model) ->
          {
            objects: (
              new TestResult(_.extend(obj, {loaded: true})) \
              for obj in eval(\
                "resp.data.#{TestResult.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(url, resolver, opts)

      $get_examples_csv: (show) ->
        url = @examplesCsvUrl() + '?show=' + show
        resolver = (resp) -> { url: resp.data['url'] }
        TestResult.$make_all_request(url, resolver)

      $get_exports: () ->
        url = "#{@BASE_API_URL}#{@id}/action/exports/"
        @$make_request(url, {}, "GET", {})

    return TestResult
])