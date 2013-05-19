angular.module('app.datas.model', ['app.config'])

.factory('Data', [
  '$http'
  '$q'
  'settings'
  'BaseModel'

  ($http, $q, settings, BaseModel) ->

    class Data extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}models/"
      BASE_UI_URL: '/models/'
      API_FIELDNAME: 'data'

      _id: null
      created_on: null
      model_name: null
      model_id: null
      test_name: null
      test_id: null
      data_input: null
      weighted_data_input: null
      _id: null

      constructor: (opts) ->
        super opts
        @BASE_API_URL = "#{settings.apiUrl}models/#{@model_id}
/tests/#{@test_id}/examples/"
        @BASE_UI_URL = "/models/#{@model_id}/tests/#{@test_id}/examples/"

      @$loadAll: (model_id, test_id, opts) ->
        if not model_id or not test_id
          throw new Error "Model and Test ids are required to load examples"

        url = "#{settings.apiUrl}models/#{model_id}/tests/#{test_id}/examples"
        resolver = (resp, Model) ->
          {
            page: resp.data.page
            total: resp.data.total
            per_page: resp.data.per_page
            objects: (
              new Model(_.extend(obj, {loaded: true})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(url, resolver, opts)

      @$loadAllGroupped: (opts) ->
        dfd = $q.defer()
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}model/#{opts.model_name}/test/
#{opts.test_name}/action/groupped/data?field=#{opts.field}&count=#{opts.count}"
          headers: settings.apiRequestDefaultHeaders
          params: opts
        )
        .then ((resp) =>
          dfd.resolve {
            field_name: resp.data['field_name']
            mavp: resp.data['mavp']
            objects: resp.data['datas'].items
          }
        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return Data
])