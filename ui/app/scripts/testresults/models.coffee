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
      @MAIN_FIELDS: 'name,status,created_on,created_by,test_in_progress'
      @MATRIX_FIELDS: ['metrics','confusion_matrix_calculations',
                       'model'].join(',')
      @EXTRA_FIELDS: ['classes_set', 'created_on','parameters','error',
                           'examples_count','dataset','memory_usage',
                           'created_by', 'examples_placement','examples_fields',
                           'examples_size'].join(',')


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
        @BASE_API_URL = TestResult.$get_api_url({
          'model_id': @model_id}, @)
        @BASE_UI_URL = "/models/#{@model_id}/tests"

      @$get_api_url: (opts, model) ->
        model_id = opts.model_id
        if model? then model_id = model_id || model.model_id
        if not model_id then throw new Error 'model_id is required'
        return "#{settings.apiUrl}models/#{model_id}/tests/"

      objectUrl: =>
        return "#{@BASE_UI_URL}/#{@id}"

      examplesUrl: =>
        return "#{@BASE_UI_URL}/#{@id}?action=examples:list"

      examplesCsvUrl: () ->
        return "#{@BASE_API_URL}#{@id}/examples/action/csv_task/"

      examplesDbUrl: () ->
        return "#{@BASE_API_URL}#{@id}/examples/action/db_task/"

      averagePrecisionUrl: =>
        return "#{@BASE_UI_URL}/#{@id}/grouped_examples"

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
        @$make_all_request(
          TestResult.$get_api_url({'model_id': model_id}), resolver, opts)

      $get_confusion_matrix: (weights) ->
        url = "#{@BASE_API_URL}#{@id}/action/confusion_matrix/"
        data = {weights: {"weights_list": weights}}
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

      $get_examples_csv: (fields) ->
        """
        @fields: array of strings of fields to export to csv
        """
        url = @examplesCsvUrl()
        resolver = (resp) -> { url: resp.data['url'] }
        @$make_request(url, {}, 'PUT',
          {fields: angular.toJson(fields)}, false)

      $get_examples_db: (opts) ->
        """
        @opts.fields: array of strings of fields to export to database
        @opts.datasource: predefined datasource to use to connect to db
        """
        opts.fields = angular.toJson(opts.fields)
        url = @examplesDbUrl()
        resolver = (resp) -> { url: resp.data['url'] }
        @$make_request(url, {}, 'PUT', opts, false)

      $get_exports: () ->
        url = "#{@BASE_API_URL}#{@id}/action/exports/"
        @$make_request(url, {}, "GET", {})

    return TestResult
])