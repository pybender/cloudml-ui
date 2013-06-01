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

      constructor: (opts) ->
        super opts
        @BASE_API_URL = DataSet.$get_api_url(@import_handler_id)

      @$get_api_url: (handler_id) ->
        return "#{settings.apiUrl}importhandlers/#{handler_id}/datasets/"

      $save: (data) =>
        @$make_request(@BASE_API_URL, data, 'POST', {})


      @$loadAll: (handler_id, opts) ->
        if not handler_id
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

    return DataSet
])
