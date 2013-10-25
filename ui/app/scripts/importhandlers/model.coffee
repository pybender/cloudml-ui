angular.module('app.importhandlers.model', ['app.config'])

.factory('ImportHandler', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
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
      data: null

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

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
