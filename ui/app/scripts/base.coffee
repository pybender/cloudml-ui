angular.module('app.base', ['app.config'])

.factory('BaseModel', [
  '$http'
  '$q'
  'settings'
  'auth'
  
  ($http, $q, settings, $auth) ->

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
            total: resp.data.total
            pages: resp.data.pages
            has_prev: resp.data.has_prev
            has_next: resp.data.has_next
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
        typeIsArray = Array.isArray || ( value ) ->
            return {}.toString.call( value ) is '[object Array]'

        if !opts.only?
          opts.only = @DEFAULT_FIELDS_TO_SAVE

        data = {}
        for name in opts.only
          val = eval("this." + name)
          if typeIsArray val then val = JSON.stringify(val)

          if val? then data[name] = val

        method = if @isNew() then "POST" else "PUT"
        @$make_request(@BASE_API_URL + (@_id + "/" or ""), {}, method, data)

      # Removes object by id
      $delete: (opts={}) =>
        $http(
          method: "DELETE"
          headers: {'Content-Type':undefined, 'X-Requested-With': null,
          'X-Auth-Token': $auth.get_auth_token()}
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
          headers: {'Content-Type': undefined, 'X-Requested-With': null,
          'X-Auth-Token': $auth.get_auth_token()}
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
          headers: _.extend(settings.apiRequestDefaultHeaders, {
            'X-Auth-Token': $auth.get_auth_token()})
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve resolver(resp, @)
        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

    return BaseModel
])