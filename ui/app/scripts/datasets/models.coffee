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

      @STATUS_IMPORTING = 'Importing'
      @STATUS_UPLOADING = 'Uploading'
      @STATUS_IMPORTED= 'Imported'

      @MAIN_FIELDS: 'name,status,import_handler_type,import_handler_id'
      @EXTRA_FIELDS: ['created_on,updated_on','data','on_s3','import_params',
                      'error','filesize','records_count','time','created_by',
                      'format', 'cluster', 'pig_step', 'pig_row']

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
      import_handler_type: 'xml'
      samples: null
      samples_json: null

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
        @BASE_UI_URL = "/importhandlers/#{@import_handler_type.toLowerCase()}/" +
                      "#{@import_handler_id}/datasets"

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
        me = @
        base_url = @constructor.$get_api_url({}, @)
        url = "#{base_url}#{@id}/action/reupload/"
        @$make_request(url, {}, "PUT", {})
        .then (resp) ->
          me.status = resp.data.dataset.status

      $reimport: =>
        me = @
        base_url = @constructor.$get_api_url({}, @)
        if @status in [DataSet.STATUS_IMPORTING, DataSet.STATUS_UPLOADING]
          throw new Error "Can't re-import a dataset that is importing now"

        url = "#{base_url}#{@id}/action/reimport/"
        @$make_request url, {}, "PUT", {}
        .then (resp) ->
          me.status = resp.data.data_set.status

      $getSampleData: ->
        base_url = @constructor.$get_api_url({}, @)
        @$make_request("#{base_url}#{@id}/action/sample_data/",
          {size:5}, 'GET')

      getPigFields: () =>
        base_url = @constructor.$get_api_url({}, @)
        url = "#{base_url}#{@id}/action/pig_fields/"
        @$make_request(url, {}, "GET", {})

    return DataSet
])
