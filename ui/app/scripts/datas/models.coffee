angular.module('app.datas.model', ['app.config'])

.factory('Data', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'TestResult'

  ($http, $q, settings, BaseModel, Test) ->

    class Data extends BaseModel
      API_FIELDNAME: 'test_example'

      id: null
      example_id: null
      created_on: null
      model_name: null
      model_id: null
      test_name: null
      test_id: null
      data_input: null
      weighted_data_input: null

      constructor: (opts) ->
        super opts
        @BASE_API_URL = Data.$get_api_url({
          'model_id': @model_id
          'test_id': @test_id}, @)
        @BASE_UI_URL = "/models/#{@model_id}/tests/#{@test_id}/examples/"

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.data_input?
            @raw_data = angular.toJson(
              angular.fromJson(origData.data_input), pretty=true)
          if origData.test_result?
            @test_result = new Test(origData['test_result'])

            if @prob? && @test_result.classes_set?
              @probChartData = []
              for p, i in @prob
                @probChartData.push {
                  value: p, label: @test_result.classes_set[i]}

      isLoadedToS3: ->
        if !@loaded
          return null

        if !@test? || @test_result.examples_placement != 'Amazon S3'
          return null

        if @weighted_data_input?
          if Object.keys(@weighted_data_input).length != 0
            return true
        return @test_result.status != 'Storing'

      @$get_api_url: (opts, model) ->
        model_id = opts.model_id
        test_id = opts.test_id
        if model?
          model_id = model_id || model.model_id
          test_id = test_id || model.test_id
        if not model_id then throw Error 'model_id is required'
        if not test_id then throw Error 'test_id is required'
        return "#{settings.apiUrl}models/#{model_id}/tests/#{test_id}/examples/"

      @$loadAll: (model_id, test_id, opts) ->
        if not model_id or not test_id
          throw new Error "Model and Test ids are required to load examples"

        url = Data.$get_api_url({
          'model_id': model_id
          'test_id': test_id})
        resolver = (resp, Model) ->
          extra_data = {loaded: true, model_id: model_id, test_id: test_id}
          {
            page: resp.data.page
            total: resp.data.total
            per_page: resp.data.per_page
            pages: resp.data.pages
            objects: (
              new Model(_.extend(obj, extra_data)) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(url, resolver, opts)

      @$loadFieldList: (model_id, test_id) ->
        if not model_id or not test_id
          throw new Error "Model and Test ids are required to load data fields"

        url = Data.$get_api_url({
          'model_id': model_id
          'test_id': test_id}) + 'action/datafields/'
        resolver = (resp) -> { fields: resp.data['fields'] }
        @$make_all_request(url, resolver, {})

      @$loadAllGroupped: (model_id, test_id, opts) ->
        if not model_id or not test_id
          throw new Error "Model and Test ids are required to load examples"

        url = Data.$get_api_url({
          'model_id': model_id
          'test_id': test_id}) + 'action/groupped/'
        resolver = (resp, Model) ->
          {
            field_name: resp.data['field_name']
            mavp: resp.data['mavp']
            objects: resp.data['test_examples'].items
          }
        @$make_all_request(url, resolver, opts)

      objectUrl: =>
        return "#{@BASE_UI_URL}/#{@id}"

      listUrl: =>
        return "/models/#{@model_id}/tests/#{@test_id}?action=examples:list"

    return Data
])