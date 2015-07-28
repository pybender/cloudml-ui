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
      @MAIN_FIELDS: 'name,id,type,db,created_on,created_by,can_edit,can_delete'
      @$VENDORS_LIST: ['postgres', ]

      id: null
      name: null
      type: null
      conn: null
      vendor: null
      created_on: null
      updated_on: null

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          if origData.db?
            @vendor = origData.db['vendor']
            @conn = origData.db['conn']

      $save: (opts={}) =>
        if !opts.extraData?
          opts.extraData = {}
        opts.extraData.db = JSON.stringify({'vendor': @vendor, 'conn': @conn})
        super opts

    return DataSource
])
