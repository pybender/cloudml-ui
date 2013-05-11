angular.module('app.models.model', ['app.config'])

.factory('Model', [
  '$http'
  '$q'
  'settings'
  
  ($http, $q, settings) ->
    ###
    Trained Model
    ###
    class Model

      constructor: (opts) ->
        @loadFromJSON opts

      _id: null
      # Unix time of model creation
      created_on: null
      status: null
      name: null
      trainer: null
      importParams: null
      negative_weights: null
      negative_weights_tree: null
      positive_weights: null
      positive_weights_tree: null
      latest_test: null
      importhandler: null
      train_importhandler: null
      features: null

      ### API methods ###

      objectUrl: =>
        return '/models/' + @name

      isNew: -> if @_id == null then true else false

      # Returns an object of job properties, for use in e.g. API requests
      # and templates
      toJSON: =>
        importhandler: @importhandler
        trainer: @trainer
        features: @features

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data
        if origData?
          @created_on = String(origData['created_on'])
          #if 'features' in origData
          @features = angular.toJson(origData['features'], pretty=true)
          #if 'importhandler' in origData
          @importhandler = angular.toJson(origData['importhandler'],
                                        pretty=true)
          #if 'train_importhandler' in origData
          @train_importhandler = angular.toJson(
              origData['train_importhandler'], pretty=true)

      $load: (opts) ->
        if @name == null
          throw new Error "Can't load model without name"

        $http(
          method: 'GET'
          url: settings.apiUrl + "model/#{@name}"
          headers:
            'X-Requested-With': null
          params: _.extend {
          }, opts
        ).then ((resp) =>
          @loaded = true
          @loadFromJSON(resp.data['model'])
          return resp

        ), ((resp) =>
          return resp
        )

      prepareSaveJSON: (json) =>
        reqData = json or @toJSON()
        return reqData

      # Makes PUT or POST request to save the object. Options:
      # ``only``: may contain a list of fields that will be sent to the server
      # (only when PUTting to existing objects, API allows partial update)
      $save: (opts={}) =>
        fd = new FormData()
        fd.append("trainer", @trainer)
        fd.append("importhandler", @importhandler)
        fd.append("train_importhandler", @train_importhandler)
        fd.append("features", @features)
        $http(
          method: if @isNew() then "POST" else "PUT"
          #headers: settings.apiRequestDefaultHeaders
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          url: "#{settings.apiUrl}model/#{@name or ""}"
          data: fd
          transformRequest: angular.identity
        )
        .then((resp) => @loadFromJSON(resp.data['model']))

      $delete: (opts={}) =>
        $http(
          method: "DELETE"
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          #headers: settings.apiRequestDefaultHeaders
          url: "#{settings.apiUrl}model/#{@name}"
          transformRequest: angular.identity
        )

      # Requests all available jobs from API and return a list of
      # Job instances
      @$loadAll: (opts) ->
        dfd = $q.defer()

        $http(
          method: 'GET'
          url: "#{settings.apiUrl}model/"
          headers: settings.apiRequestDefaultHeaders
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve {
            total: resp.data.found
            objects: (
              new @(_.extend(obj, {loaded: true})) \
              for obj in resp.data.models)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

      $train: (opts={}) =>
        fd = new FormData()
        for key, val of opts
          fd.append(key, val)
        
        $http(
          method: "PUT"
          #headers: settings.apiRequestDefaultHeaders
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          url: "#{settings.apiUrl}model/#{@name}/train"
          data: fd
          transformRequest: angular.identity
        )
        .then((resp) => @loadFromJSON(resp.data['model']))

    return Model
])