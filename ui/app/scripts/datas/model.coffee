angular.module('app.datas.model', ['app.config'])

.factory('Data', [
  '$http'
  '$q'
  'settings'

  ($http, $q, settings) ->

    class Data

      constructor: (opts) ->
        @loadFromJSON opts

      id: null
      created_on: null
      model_name: null
      test_name: null
      data_input: null
      weighted_data_input: null
      _id: null

      ### API methods ###

      isNew: -> if @slug == null then true else false

      # Returns an object of job properties, for use in e.g. API requests
      # and templates
      toJSON: =>
        name: @name

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      $load: (opts) ->
        if @name == null
          throw new Error "Can't load model without name"
        
        $http(
          method: 'GET'
          url: settings.apiUrl + "model/#{@model_name}/test/
#{@test_name}/data/#{@id}"
          headers: {'X-Requested-With': null}
          params: _.extend {
          }, opts
        ).then ((resp) =>
          @loaded = true
          @loadFromJSON(resp.data['data'])
          return resp

        ), ((resp) =>
          return resp
        )

      @$loadAll: (opts) ->
        dfd = $q.defer()
        model_name = opts.model_name
        test_name = opts.test_name
        $http(
          method: 'GET'
          url: "#{settings.apiUrl}model/#{model_name}/test/
#{test_name}/data"
          headers: settings.apiRequestDefaultHeaders
          params: opts
        )
        .then ((resp) =>
          extra = {loaded: true, model_name: model_name, test_name: test_name}
          dfd.resolve {
            pages: resp.data.pages
            page: resp.data.page
            total: resp.data.total
            per_page: resp.data.per_page
            objects: (
              new @(_.extend(obj, extra)) \
              for obj in resp.data.datas)
            _resp: resp
          }

        ), (-> dfd.reject.apply @, arguments)

        dfd.promise

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