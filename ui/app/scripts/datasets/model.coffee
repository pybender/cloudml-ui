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
      API_FIELDNAME: 'data_set'

      STATUS_IMPORTING = 'Importing'
      STATUS_UPLOADING = 'Uploading'

      @MAIN_FIELDS: 'name,status,import_handler_type,import_handler_id'

      id: null
      name: null
      status: 'not loaded'
      error: ''
      created_on: null
      updated_on: null

      data: null
      import_params: null
      import_handler_id: null
      on_s3: false
      format: 'json'
      import_handler_type: 'JSON'

      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.import_handler?
            @import_handler_id = origData.import_handler.id
            @import_handler_type = origData.import_handler.TYPE
          if origData.on_s3?
            if typeof(origData.on_s3) != "boolean"
              @on_s3 = origData.on_s3 == 'True'

      constructor: (opts) ->
        super
        @BASE_API_URL = DataSet.$get_api_url(
          @import_handler_id, @import_handler_type)
        @BASE_UI_URL = "/handlers/
#{@import_handler_type.toLowerCase()}/#{@import_handler_id}/datasets/"

      @$get_api_url: (handler_id, handler_type) ->
        return "#{settings.apiUrl}importhandlers/#{handler_type.toLowerCase()}\
/#{handler_id}/datasets/"

      $generateS3Url: () =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/generate_url/",
                       {}, 'GET', {})

      $save: (data) =>
        if data.only
          super data
        else
          @$make_request(@BASE_API_URL, {}, 'POST', data)

      @$loadAll: (opts) ->
        if not opts.import_handler_id? || not opts.import_handler_id?
          throw new Error "Import Handler is required to load datasets"

        resolver = (resp, Model) ->
          extra = {
            loaded: true
            import_handler_id: opts.import_handler_id
            import_handler_type: opts.import_handler_type}
          {
            objects: (
              new DataSet(_.extend(obj, extra)) \
              for obj in eval("resp.data.#{DataSet.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        url = DataSet.$get_api_url(
          opts.import_handler_id, opts.import_handler_type)
        @$make_all_request(url, resolver, opts)

      $reupload: =>
        url = "#{@BASE_API_URL}#{@id}/action/reupload/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.dataset.status)

      $reimport: =>
        if @status in [@STATUS_IMPORTING, @STATUS_UPLOADING]
          throw new Error "Can't re-import a dataset that is importing now"

        url = "#{@BASE_API_URL}#{@id}/action/reimport/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.dataset.status)

    return DataSet
])
