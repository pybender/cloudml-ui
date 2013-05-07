angular.module('app.importhandlers.model', ['app.config'])

.factory('ImportHandler', [
  '$http'
  '$q'
  'settings'
  
  ($http, $q, settings) ->
    ###
    Import Handler
    ###
    class ImportHandler

      constructor: (opts) ->
        @loadFromJSON opts

      id: null
      created_on: null
      updated_on: null
      name: null
      type: null
      data: null

      ### API methods ###

      objectUrl: =>
        return '/import_handlers/' + @name

      isNew: -> if @id == null then true else false

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data
        if origData?
          @data = angular.toJson(origData['data'],
                                        pretty=true)

      $load: (opts) ->
        if @name == null
          throw new Error "Can't load import handler model without name"

        $http(
          method: 'GET'
          url: "#{settings.apiUrl}import/handler/#{@name}"
          headers:
            'X-Requested-With': null
          params: _.extend {
          }, opts
        ).then ((resp) =>
          @loaded = true
          @loadFromJSON(resp.data['import_handler'])
          return resp

        ), ((resp) =>
          return resp
        )

      $save: (opts={}) =>
        fd = new FormData()
        fd.append("name", @name)
        fd.append("type", @type['name'])
        fd.append("data", @data)
        $http(
          method: if @isNew() then "POST" else "PUT"
          #headers: settings.apiRequestDefaultHeaders
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          url: "#{settings.apiUrl}import/handler/#{@name or ""}"
          data: fd
          transformRequest: angular.identity
        )
        .then((resp) => @loadFromJSON(resp.data['import_handler']))

      # Requests all available import handlers from API and return a
      # list of ImportHandler instances
      @$loadAll: (opts) ->
        dfd = $q.defer()

        $http(
          method: 'GET'
          url: "#{settings.apiUrl}import/handler/"
          headers: settings.apiRequestDefaultHeaders
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve {
            total: resp.data.found
            objects: (
              new @(_.extend(obj, {loaded: true})) \
              for obj in resp.data.import_handlers)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return ImportHandler
])