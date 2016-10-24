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
      DEFAULT_FIELDS_TO_SAVE: ['name', 'descriptions', 'scenarios', 'interval',
                               'enabled', 'crontab', 'type']
      @MAIN_FIELDS: ['id','name','created_on','updated_on','enabled','descriptions',
                    'scenarios','interval','crontab','created_by','type'].join(',')

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
      name: null
      scenariosDict: []
      intervalDict: {}
      crontabDict: {}

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.scenarios?
            @scenariosDict.splice(0, @scenariosDict.length)
            @scenariosDict.push origData['scenarios']
          if origData.interval?
            @intervalDict = origData['interval']
          if origData.crontab?
            @crontabDict = origData['crontab']


      $save: (opts={}) =>
        if opts.only? && "interval" in opts.only
          if @type == 'crontab'
            @intervalDict = {}
          @interval = JSON.stringify(@intervalDict)

        if opts.only? && "crontab" in opts.only
          if @type == 'interval'
            @crontabDict = {}
          @crontab = JSON.stringify(@crontabDict)

        if opts.only? && "scenarios" in opts.only
          @scenarios = JSON.stringify(@scenariosDict[0])

        super opts

      $getConfiguration: (opts={}) =>  # TODO: into mixin
        base_url = @constructor.$get_api_url(opts, @)
        @$make_request("#{base_url}action/configuration/",
                       load=false)

    return Schedule
])