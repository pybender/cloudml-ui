angular.module('app.weights.model', ['app.config'])

.factory('Weight', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Model Parameter Weight
    ###
    class Weight extends BaseModel
      id: null
      name: null
      model_name: null
      model_id: null
      value: null

      @$loadAll: (model_id, opts) ->
        dfd = $q.defer()

        if not model_id then throw new Error "Model is required to load weights"
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}weights/#{model_id}/"
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

      @$loadBriefList: (model_id, opts) ->
        dfd = $q.defer()

        if not model_id then throw new Error "Model is required to weights list"
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}weights/#{model_id}/action/brief/"
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
            negative: (new Weight(obj) for obj in resp.data.negative_weights)
            positive: (new Weight(obj) for obj in resp.data.positive_weights)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return Weight
])

.factory('Category', [
  '$http'
  '$q'
  'settings'
  
  ($http, $q, settings) ->
    ###
    Model Parameter WeightsCategory
    ###
    class Category
      constructor: (opts) ->
        @loadFromJSON opts

      id: null
      name: null
      model_name: null
      short_name: null
      parent: null

      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

    return Category
])

.factory('WeightsTree', [
  '$http'
  '$q'
  'settings'
  'Category'
  'Weight'
  
  ($http, $q, settings, Category, Weight) ->
    ###
    Model Parameter WeightsCategory
    ###
    class WeightsTree
      constructor: (opts) ->
        @loadFromJSON opts

      id: null
      name: null
      model_name: null
      short_name: null
      parent: null

      ### API methods ###

      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      @$loadNode: (modelName, opts) ->
        dfd = $q.defer()

        if not modelName then throw new Error "Model is required to load tests"
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}weights_tree/#{modelName}"
          headers: settings.apiRequestDefaultHeaders
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve {
            categories: (new Category(obj) for obj in resp.data.categories)
            weights: (new Weight(obj) for obj in resp.data.weights)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return WeightsTree
])