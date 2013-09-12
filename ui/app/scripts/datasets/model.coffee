angular.module('app.datasets.model', ['app.config'])

.factory('DataSet', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    DataSet
    ###
    class DataSet extends BaseModel
      API_FIELDNAME: 'dataset'

      _id: null
      name: null
      status: 'not loaded'
      error: ''
      created_on: null
      updated_on: null

      data: null
      import_params: null
      import_handler_id: null
      on_s3: false


      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.on_s3?
            if typeof(origData.on_s3) != "boolean"
              @on_s3 = origData.on_s3 == 'True'

      constructor: (opts) ->
        super
        @BASE_API_URL = DataSet.$get_api_url(@import_handler_id)
        @BASE_UI_URL = "/importhandlers/#{@import_handler_id}/datasets/"

      @$get_api_url: (handler_id) ->
        return "#{settings.apiUrl}importhandlers/#{handler_id}/datasets/"

      $generateS3Url: () =>
        @$make_request("#{@BASE_API_URL}#{@_id}/action/generate_url/",
                       {}, 'GET', {})

      $save: (data) =>
        if data.only
          super data
        else
          @$make_request(@BASE_API_URL, data, 'POST', {})

      @$loadAll: (opts) ->
        handler_id = opts.handler_id
        if not handler_id?
          throw new Error "Import Handler is required to load datasets"

        resolver = (resp, Model) ->
          extra = {loaded: true, import_handler_id: handler_id}
          {
            objects: (
              new DataSet(_.extend(obj, extra)) \
              for obj in eval("resp.data.#{DataSet.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(DataSet.$get_api_url(handler_id), resolver, opts)

      $reupload: =>
        url = "#{@BASE_API_URL}#{@_id}/action/reupload/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.dataset.status)

    return DataSet
])
