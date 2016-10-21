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
      DEFAULT_FIELDS_TO_SAVE: ['name', 'description', 'scenarios', 'interval',
                               'enabled', 'crontab']
      @LIST_MODEL_NAME: 'schedules'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      SCHEDULE_TYPES: ['crontab', 'interval']
      CRONTAB_CONFIG: [{name: 'minute', type: 'string', default: '*'},
                       {name: 'hour', type: 'string', default: '*'},
                       {name: 'day_of_week', type: 'string', default: '*'},
                       {name: 'day_of_month', type: 'string', default: '*'},
                       {name: 'month_of_year', type: 'string', default: '*'}]
      INTERVAL_CONFIG: [{name:'every', type: 'integer'},
                        {name: 'period', type: 'string', choices: ['microseconds', 'seconds', 'minutes', 'hours', 'days']}]
      TASK_TYPES: ['single', 'chain', 'chord', 'group']

      id: null
      created_on: null
      updated_on: null
      created_by: null
      updated_by: null
      name: null
      description: null
      scenarios: []
      interval: {}
      crontab: {}
      type: null
      enabled: null

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.scenarios?
            @scenarios = array(origData['scenarios'])
            console.log @scenarios
          if origData.interval?
            @type = 'interval'
          else
            @type = 'crontab'


      $save: (opts={}) =>
        console.log opts.only
        console.log @
        if opts.only? && "interval" in opts.only
          @interval = angular.toJson(@interval)

        if opts.only? && "crontab" in opts.only
          @crontab = angular.toJson(@crontab)

        if opts.only? && "scenarios" in opts.only
          @scenarios = @scenarios[0]
          @scenarios = angular.toJson(@scenarios)

        super opts

      $getConfiguration: (opts={}) =>  # TODO: into mixin
        base_url = @constructor.$get_api_url(opts, @)
        @$make_request("#{base_url}action/configuration/",
                       load=false)

    return Schedule
])