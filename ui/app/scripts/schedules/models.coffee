angular.module('app.schedules.model', ['app.config'])

.factory('Schedule', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Periodic Task Schedule
    ###
    class Schedule  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}schedules/"
      BASE_UI_URL: '/schedules'
      API_FIELDNAME: 'schedule'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'description', 'scenario', 'type',
                               'enabled', 'schedule']
      id: null
      created_on: null
      updated_on: null
      name: null
      type: null
      description: null
      scenario: null
      schedule: null
      type: null
      enabled: null

      loadFromJSON: (origData) =>
        super origData

      $save: (opts={}) =>
        if opts.only? && "type" in opts.only
          @type = @type['name']
        super opts

    return Schedule
])