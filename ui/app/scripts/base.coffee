angular.module('app.base', ['app.config', 'app.services'])


.factory('BaseModel', [
  '$http'
  '$q'
  'settings'
  'auth'
  '$rootScope'
  
  ($http, $q, settings, auth, $rootScope) ->
    transformRequest = (data, headersGetter) ->
      $rootScope.loadingCount += 1
      $rootScope.$broadcast('httpCallStarted')
      return data

    transformResponse = (data, headersGetter) ->
      $rootScope.loadingCount -= 1
      $rootScope.$broadcast('httpCallStopped')
      if data
        Number.prototype.formatMoney = () ->
          return this.baseValue
        return JSON.parse(data)
      return data

    class BaseModel
      BASE_UI_URL: ''
      BASE_API_URL: ''
      API_FIELDNAME: 'object'
      DEFAULT_FIELDS_TO_SAVE = []
      DATA_FIELDS: []

      constructor: (opts) ->
        @loadFromJSON opts

      # Returns object details url in UI
      objectUrl: =>
        return "#{@BASE_UI_URL}/#{@id}"

      # Checks whether object saved to db
      isNew: -> if @id == null then true else false

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      getJsonData: () =>
        data = {}
        for key in @DATA_FIELDS
          val = eval('this.' + key)
          if val? && val != ""
            data[key] = val
        return data

      @$get_api_url: (opts, model) ->
        return @prototype.BASE_API_URL

      #
      # Loads list of objects related methods
      #
      @$loadAll: (opts) ->
        extra = @$beforeLoadAll(opts)
        resolver = @$buildLoadAllResolver(opts, extra)
        url = @$get_api_url(opts)
        @$make_all_request(url, resolver, opts)

      @$beforeLoadAll: (opts) ->
        # Use it to validate opts
        return {}

      @$buildLoadAllResolver: (opts, extra) ->
        return (resp, Model) ->
          {
            total: resp.data.total
            pages: resp.data.pages
            has_prev: resp.data.has_prev
            has_next: resp.data.has_next
            objects: (
              new Model(_.extend(obj, {loaded: true}, extra)) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }

      #
      # Loads specific object details
      #
      $load: (opts) ->
        if @id == null
          throw new Error "Can't load model without id"

        base_url = @constructor.$get_api_url(opts, @)
        @$make_request("#{base_url}#{@id}/", opts)

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
          if (name == 'params' or name == 'parameters') && typeof(val) == 'object'
            params = {}
            for k, p of @params
              if p? && p != ''
                params[k] = p
            @params = params
            val = JSON.stringify(@params)

          if val? then data[name] = val

        if opts.extraData?
          data = $.extend(data, opts.extraData)

        method = if @isNew() then "POST" else "PUT"
        base_url = @constructor.$get_api_url(opts, @)
        url = if @id? then base_url + @id + "/" else base_url
        @$make_request(url, {}, method, data)

      $clean_parameters: (opts={}) =>
        data = {}
        for key, val of opts
          if key == 'parameters' then val = JSON.stringify(val)

          if val?
            data[key] = val

        return data

      # Removes object by id
      $delete: (opts={}) =>
        if @id == null
          throw new Error "Can't delete model without id"

        base_url = @constructor.$get_api_url(opts, @)
        $http(
          method: "DELETE"
          headers: {'Content-Type':undefined,
          'X-Auth-Token': auth.get_auth_token()}
          url: "#{base_url}#{@id}/"
          transformRequest: angular.identity
        )

      $make_request: (url, opts={}, method='GET', data={}, load=true) =>
        fd = new FormData()
        for key, val of data
          fd.append(key, val)

        res = $http(
          method: method
          #headers: settings.apiRequestDefaultHeaders
          headers: {'Content-Type': undefined,
          'X-Auth-Token': auth.get_auth_token()}
          url: url
          data: fd
          transformRequest: transformRequest
          transformResponse: transformResponse
          params: _.extend {}, opts
        )
        if load
          res.then ((resp) =>
            @loaded = true
            if resp.data?
              @loadFromJSON(eval("resp.data.#{@API_FIELDNAME}"))
            else
              console.log('Got invalid response: ' + angular.toJson(resp, true))
            return resp
          )
        return res

      @$make_all_request: (url, resolver, opts={}) ->
        dfd = $q.defer()
        $http(
          method: 'GET'
          url: url
          transformRequest: transformRequest
          transformResponse: transformResponse
          headers: _.extend(settings.apiRequestDefaultHeaders, {
            'X-Auth-Token': auth.get_auth_token()})
          params: _.extend {
          }, opts
        )
        .then ((resp) =>
          dfd.resolve resolver(resp, @)
        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

      $getConfiguration: (opts={}) =>  # TODO: into mixin
        base_url = @constructor.$get_api_url(opts, @)
        @$make_request("#{base_url}#{@id}/action/configuration/",
                       load=false)

      @$getConfiguration: (opts) ->
        resolver = (resp, Model) ->
          {
            configuration: resp.data.configuration
            _resp: resp
          }
        @$make_all_request(
          "#{@prototype.BASE_API_URL}action/configuration/", resolver, opts)

    return BaseModel
])
