angular.module('app.weights.model', ['app.config'])

.factory('Weight', [
  '$http'
  '$q'
  'settings'
  
  ($http, $q, settings) ->
    ###
    Model Parameter Weight
    ###
    class Weight
      constructor: (opts) ->
        @loadFromJSON opts

      _id: null
      name: null
      model_name: null
      value: null

      ### API methods ###

      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      @$loadAll: (modelName, opts) ->
        dfd = $q.defer()

        if not modelName then throw new Error "Model is required to load tests"
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}weights/#{modelName}"
          headers: settings.apiRequestDefaultHeaders
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve {
            pages: resp.data.pages
            page: resp.data.page
            total: resp.data.total
            per_page: resp.data.per_page
            objects: (new Weight(obj) for obj in resp.data.weights)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return Weight
])