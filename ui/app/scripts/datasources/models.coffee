angular.module('app.datasources.model', ['app.config'])

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
