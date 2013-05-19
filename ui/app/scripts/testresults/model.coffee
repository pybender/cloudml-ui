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
        @BASE_API_URL = "#{settings.apiUrl}models/#{@model_id}/tests/"
        @BASE_UI_URL = "/models/#{@model_id || @model._id}/tests/#{@_id}"

      examplesUrl: =>
        model = @model_name || @model.name
        return "#{@BASE_UI_URL}/examples"

      fullName: =>
        if @model? || @model_name
          return (@model_name || @model.name) + " / " + @name
        return @name

      loadFromJSON: (origData) =>
        super origData
        if 'model' in origData
          @model = new Model(origData['model'])
          @model_name = origData['model']['name']

      $save: (opts={}) =>
        saveData = @toJSON()

        fields = opts.only || []
        if fields.length > 0
          for key in _.keys(saveData)
            if key not in fields
              delete saveData[key]

        saveData = @prepareSaveJSON(saveData)

        $http(
          method: if @isNew() then 'POST' else 'PUT'
          headers: settings.apiRequestDefaultHeaders
          url: "#{settings.apiUrl}/jobs/#{@id or ""}"
          params: {access_token: user.access_token}
          data: $.param saveData
        )
        .then((resp) => @loadFromJSON(resp.data))

      @$loadTests: (model_id, opts) ->
        if not model_id
          throw new Error "Model is required to load tests"

        url = "#{settings.apiUrl}models/#{model_id}/tests/"
        resolver = (resp, Model) ->
          {
            objects: (
              new Model(_.extend(obj, {loaded: true})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(url, resolver, opts)

    return TestResult
])