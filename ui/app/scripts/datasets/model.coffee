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
      samples: null

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
        #@BASE_API_URL = DataSet.$get_api_url({}, @)
        @BASE_UI_URL = "/handlers/
#{@import_handler_type.toLowerCase()}/#{@import_handler_id}/datasets/"

      @$get_api_url: (opts, model) ->
        handler_id = opts.import_handler_id
        handler_type = opts.import_handler_type
        if model?
          handler_id = handler_id || model.import_handler_id
          handler_type = handler_type || model.import_handler_type

        if not (handler_id && handler_type)
          throw new Error('import handler details are required')

        return "#{settings.apiUrl}importhandlers/#{handler_type.toLowerCase()}\
/#{handler_id}/datasets/"

      @$beforeLoadAll: (opts) ->
        return {
          'import_handler_id': opts.import_handler_id
          'import_handler_type': opts.import_handler_type
        }

      $generateS3Url: () =>
        base_url = @constructor.$get_api_url({}, @)
        @$make_request("#{base_url}#{@id}/action/generate_url/",
                       {}, 'GET', {})

      $save: (opts) =>
        if opts.only
          super opts
        else
          base_url = @constructor.$get_api_url(opts, @)
          @$make_request(base_url, {}, 'POST', opts)

      $reupload: =>
        base_url = @constructor.$get_api_url({}, @)
        url = "#{base_url}#{@id}/action/reupload/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.dataset.status)

      $reimport: =>
        base_url = @constructor.$get_api_url({}, @)
        if @status in [@STATUS_IMPORTING, @STATUS_UPLOADING]
          throw new Error "Can't re-import a dataset that is importing now"

        url = "#{base_url}#{@id}/action/reimport/"
        @$make_request(url, {}, "PUT", {}).then(
          (resp) =>
            @status = resp.data.dataset.status)

      $getSampleData: ->
        base_url = @constructor.$get_api_url({}, @)
        @$make_request("#{base_url}#{@id}/action/sample_data/",
                       {}, 'GET', {size:15})


    return DataSet
])
