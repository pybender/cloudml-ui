angular.module('app.base', ['app.config'])

.factory('BaseModel', [
  '$http'
  '$q'
  'settings'
  
  ($http, $q, settings) ->

    class BaseModel
      BASE_UI_URL: ''
      BASE_API_URL: ''
      API_FIELDNAME: 'object'
      DEFAULT_FIELDS_TO_SAVE = []

      constructor: (opts) ->
        @loadFromJSON opts

      # Returns object details url in UI
      objectUrl: =>
        return @BASE_UI_URL + @_id

      # Checks whether object saved to db
      isNew: -> if @_id == null then true else false

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      # Loads list of objects
      @$loadAll: (opts) ->
        resolver = (resp, Model) ->
          {
            total: resp.data.found
            objects: (
              new Model(_.extend(obj, {loaded: true})) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request("#{@prototype.BASE_API_URL}", resolver, opts)

      # Loads specific object details
      $load: (opts) ->
        if @_id == null
          throw new Error "Can't load model without id"
        @$make_request("#{@BASE_API_URL}#{@_id}/", opts)

      # Saves or creates the object
      $save: (opts={}) =>
        if !opts.only?
          opts.only = @DEFAULT_FIELDS_TO_SAVE

        data = {}
        for name in opts.only
          data[name] = eval("this." + name)

        method = if @isNew() then "POST" else "PUT"
        @$make_request(@BASE_API_URL + (@_id + "/" or ""), {}, method, data)

      # Removes object by id
      $delete: (opts={}) =>
        $http(
          method: "DELETE"
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          url: "#{@BASE_API_URL}#{@_id}/"
          transformRequest: angular.identity
        )

      $make_request: (url, opts={}, method='GET', data={}) =>
        fd = new FormData()
        for key, val of data
          fd.append(key, val)
        
        $http(
          method: method
          #headers: settings.apiRequestDefaultHeaders
          headers: {'Content-Type':undefined, 'X-Requested-With': null}
          url: url
          data: fd
          transformRequest: angular.identity
          params: _.extend {
          }, opts
        ).then ((resp) =>
          @loaded = true
          @loadFromJSON(eval("resp.data.#{@API_FIELDNAME}"))
          return resp
        )

      @$make_all_request: (url, resolver, opts={}) ->
        dfd = $q.defer()
        $http(
          method: 'GET'
          url: url
          headers: settings.apiRequestDefaultHeaders
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve resolver(resp, @)
        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return BaseModel
])