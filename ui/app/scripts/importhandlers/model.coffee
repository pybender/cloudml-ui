angular.module('app.importhandlers.model', ['app.config'])

.factory('Item', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Item  extends BaseModel
      source: null
      target_features: []
      process_as: null
      is_required: null

      handler: null
      query_num: null
      num: null

      loadFromJSON: (origData) =>
        super origData
        if origData?
          data = {
            'target_schema': @target_schema,
            'queries': @queries,
            'sql': @sql}
          if @datasource?
            data['datasource'] = @datasource.toJson()
          @data = angular.toJson(data, pretty=true)

      $save: (opts={}) =>
        prefix = 'queries.' + @query_num + '.items.' + @num + '.'
        if !opts.only?
          opts.only = ['source', 'process_as', 'is_required']
        data = {}
        for key in opts.only
          data[prefix + key] = eval('this.' + key)
        @$make_request(@handler.getUrl(), {}, "PUT", data)

    return Item
])

.factory('Query', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Item'
  
  ($http, $q, settings, BaseModel, Item) ->
    class Query  extends BaseModel
      name: null
      sql: null
      items: []

      handler: null
      num: null

      loadFromJSON: (origData) =>
        super origData
        if origData?
          data = {
            'target_schema': @target_schema,
            'queries': @queries,
            'sql': @sql}
          if @datasource?
            data['datasource'] = @datasource.toJson()
          @data = angular.toJson(data, pretty=true)

          i = 0
          if origData.items?
            @items = []
            for queryData in origData.items
              @items.push new Item(
                _.extend queryData, {
                  'handler': @handler, 'num': i, 'query_num': @num})
              i += 1

      $save: (opts={}) =>
        prefix = 'queries.' + @num + '.'
        data = {}
        for key in opts.only
          data[prefix + key] = eval('this.' + key)
        @$make_request(@handler.getUrl(), {}, "PUT", data)

    return Query
])


.factory('ImportHandler', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Query'
  
  ($http, $q, settings, BaseModel, Query) ->
    ###
    Import Handler
    ###
    class ImportHandler  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}importhandlers/"
      BASE_UI_URL: '/importhandlers/'
      API_FIELDNAME: 'import_handler'
      @MAIN_FIELDS: 'name,_id,target_schema,import_parameters,
created_on,created_by,datasource__name'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'data']

      @PROCESS_STRATEGIES = ['identity', 'string', 'float',
        'boolean', 'integer', 'json', 'composite']

      _id: null
      created_on: null
      updated_on: null
      name: null
      target_schema: null
      import_params: null
      datasource: null
      queries: []

      getUrl: =>
        return "#{@BASE_API_URL}#{@_id || ''}/"

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

      loadFromJSON: (origData) =>
        super origData
        if origData?
          data = {
            'target_schema': @target_schema,
            'queries': @queries,
            'sql': @sql}
          @data = angular.toJson(data, pretty=true)

          if @datasource?
            data['datasource'] = @datasource.toJson()

          i = 0
          if origData.queries?
            @queries = []
            for queryData in origData.queries
              @queries.push new Query(
                _.extend queryData, {'handler': @, 'num': i})
              i += 1

      $save: (opts={}) =>
        #@type = @type['name']
        super opts

      $loadData: (opts={}) =>
        # Executes loading dataset task
        data = {}
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@_id}/action/load/", {}, "PUT", data)

    return ImportHandler
])


.factory('DataSource', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Data Source
    ###
    class DataSource  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}datasources/"
      API_FIELDNAME: 'datasource'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'type']
      @LIST_MODEL_NAME: 'datasources'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @$TYPES_LIST: ['sql', ]
      @MAIN_FIELDS: 'name,_id,type,db_settings,created_on,created_by'
      @$VENDORS_LIST: ['postgres', ]

      _id: null
      name: null
      type: null
      db_settings: {'conn': '', 'vendor': ''}
      created_on: null
      updated_on: null

      $save: (opts={}) =>
        if @db_settings? && typeof(@db_settings) == 'object'
          @db_settings = JSON.stringify(@db_settings)
        super opts

    return DataSource
])
