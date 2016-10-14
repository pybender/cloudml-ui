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
      BASE_API_URL: "#{settings.apiUrl}schedule/"
      BASE_UI_URL: '/schedule'
      API_FIELDNAME: 'schedule'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'description', 'scenario', 'type',
                               'enabled', 'schedule']
      id: null
      created_on: null
      updated_on: null
      name: null
      type: null
      description: null
      scenario: {}
      schedule: {}
      type: null
      enabled: null

      loadFromJSON: (origData) =>
        super origData

      $save: (opts={}) =>
        console.log opts.only
        console.log @
        if opts.only? && "type" in opts.only
          @type = @type['name']

        if opts.only? && "scenario" in opts.only
          @scenario = angular.toJson(@scenario)

        if opts.only? && "schedule" in opts.only
          @schedule = angular.toJson(@schedule)

        super opts

      $getConfiguration: (opts={}) =>  # TODO: into mixin
        base_url = @constructor.$get_api_url(opts, @)
        @$make_request("#{base_url}action/task_configuration/",
                       load=false)

    return Schedule
])