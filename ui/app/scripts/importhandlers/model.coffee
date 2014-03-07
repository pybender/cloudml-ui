angular.module('app.importhandlers.model', ['app.config'])

.factory('TargetFeature', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class TargetFeature  extends BaseModel
      DATA_FIELDS: ['name', 'jsonpath', 'to_csv', 'key_path',
      'value_path']
      name: null
      jsonpath: null
      to_csv: null
      key_path: null
      value_path: null

      handler: null
      item_num: null
      query_num: null
      num: null

      isNew: -> @num == -1

      $save: (opts={}) =>
        prefix = 'queries.' + @query_num + '.items.'\
        + @item_num + '.target_features.' + @num + '.'

        if !opts.only?
          opts.only = @DATA_FIELDS
        data = {}
        for key in opts.only
          val = eval('this.' + key)
          if key == 'expression'
            val = JSON.stringify(val)
          data[prefix + key] = val
        @$make_request(@handler.getUrl(), {}, "PUT", data)

      $remove: () ->
        data = {
          'remove_feature': 1
          'num': @num
          'item_num': @item_num
          'query_num': @query_num}
        @$make_request(@handler.getUrl(), {}, "PUT", data)

    return TargetFeature
])


.factory('Item', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'TargetFeature'
  
  ($http, $q, settings, BaseModel, TargetFeature) ->
    class Item  extends BaseModel
      DATA_FIELDS: ['source', 'process_as', 'is_required']
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
          i = 0
          if origData.target_features?
            @target_features = []
            for queryData in origData.target_features
              @target_features.push new TargetFeature(
                _.extend queryData, {
                  'handler': @handler,
                  'num': i,
                  'query_num': @query_num,
                  'item_num': @num}
              )
              i += 1

      getJsonData: () =>
        data = super()
        data['target_features'] = []
        for feature in @target_features
          data['target_features'].push feature.getJsonData()
        return data

      $save: (opts={}) =>
        prefix = 'queries.' + @query_num + '.items.' + @num + '.'
        if !opts.only?
          opts.only = ['source', 'process_as', 'is_required']
        data = {}
        for key in opts.only
          data[prefix + key] = eval('this.' + key)
        @$make_request(@handler.getUrl(), {}, "PUT", data)

      $remove: () ->
        data = {'remove_item': 1, 'num': @num, 'query_num': @query_num}
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
      DATA_FIELDS: ['name', 'sql']
      name: null
      sql: null
      items: []

      handler: null
      num: null

      getJsonData: () =>
        data = super()
        data['items'] = []
        for i in @items
          data['items'].push i.getJsonData()
        return data

      loadFromJSON: (origData) =>
        super origData
        if origData?
          i = 0
          if origData.items?
            @items = []
            for queryData in origData.items
              @items.push new Item(
                _.extend queryData, {
                  'handler': @handler, 'num': i, 'query_num': @num}
              )
              i += 1

      $save: (opts={}) =>
        prefix = 'queries.' + @num + '.'
        data = {}
        for key in opts.only
          data[prefix + key] = eval('this.' + key)
        _handler = @handler
        @$make_request(@handler.getUrl(), {}, "PUT", data).then((resp) ->
          _handler.loadFromJSON(resp.data['import_handler'])
        )

      $remove: () ->
        data = {'remove_query': 1, 'num': @num}
        @$make_request(@handler.getUrl(), {}, "PUT", data)

      getParams: () ->
        expr = /%\((\w+)\)s/gi
        params = []
        matches = expr.exec(@sql)
        while matches
          params.push matches[1]
          matches = expr.exec(@sql)
        return params

      $run: (limit, params, datasource) ->
        data = {
          sql: @sql,
          params: JSON.stringify(params),
          limit: limit,
          datasource: datasource
        }
        @$make_request(@handler.getUrl() + 'action/run_sql/', {}, "PUT", data)

    return Query
])


.factory('ImportHandler', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Query'
  'DataSource'
  
  ($http, $q, settings, BaseModel, Query, DataSource) ->
    ###
    Import Handler
    ###
    class ImportHandler  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}importhandlers/"
      BASE_UI_URL: '/importhandlers/'
      API_FIELDNAME: 'import_handler'
      @MAIN_FIELDS: 'name,id,import_params,
created_on,created_by,error'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'data']
      @PROCESS_STRATEGIES = ['identity', 'string', 'float',
        'boolean', 'integer', 'json', 'composite']
      DATA_FIELDS: ['target_schema']
      TYPE: 'Simple'

      id: null
      created_on: null
      updated_on: null
      name: null
      target_schema: null
      import_params: null
      datasource: []
      queries: []
      data_json: "loading..."

      getUrl: =>
        return "#{@BASE_API_URL}#{@id || ''}/"

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@id}/action/download/"

      loadFromJSON: (origData) =>
        super origData

        if origData? && origData.data?
          @data_json = angular.toJson(origData.data, pretty=true)

          i = 0
          if origData.data.datasource?
            @datasource = []
            for dsData in origData.data.datasource
              @datasource.push new DataSource(
                _.extend dsData, {'handler': @, 'num': i})
              i += 1

          i = 0
          if origData.data.queries?
            @queries = []
            for queryData in origData.data.queries
              @queries.push new Query(
                _.extend queryData, {'handler': @, 'num': i})
              i += 1

      $loadData: (opts={}) =>
        # Executes loading dataset task
        data = {}
        return
        for key, val of opts
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@id}/action/load/", {}, "PUT", data)

      $getTestImportUrl: (params, limit) ->
        data = {
          params: JSON.stringify(params),
          limit: limit,
        }
        @$make_request("#{@BASE_API_URL}#{@id}/action/test_handler/", {},
          "PUT", data)

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
      API_FIELDNAME: 'predefined_data_source'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'type']
      @LIST_MODEL_NAME: 'datasources'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @$TYPES_LIST: ['sql', ]
      @MAIN_FIELDS: 'name,id,type,db,created_on,created_by'
      @$VENDORS_LIST: ['postgres', ]

      id: null
      name: null
      type: null
      db: {'conn': '', 'vendor': ''}
      created_on: null
      updated_on: null

      $save: (opts={}) =>
        if @handler?
          prefix = 'datasource.' + @num + '.'
          data = {}
          for key in opts.only
            val = eval('this.' + key)
            if key == 'db'
              data[prefix + key] = JSON.stringify(val)
            else
              data[prefix + key] = val
          @$make_request(@handler.getUrl(), {}, "PUT", data)
        else
          if @db? && typeof(@db) == 'object'
            @db = JSON.stringify(@db)
          super opts

    return DataSource
])
