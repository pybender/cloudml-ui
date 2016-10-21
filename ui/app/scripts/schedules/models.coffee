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
      DEFAULT_FIELDS_TO_SAVE: ['name', 'description', 'scenarios', 'interval',
                               'enabled', 'crontab']
      id: null
      created_on: null
      updated_on: null
      created_by: null
      updated_by: null
      name: null
      description: null
      scenarios: {}
      interval: {}
      crontab: {}
      type: null
      enabled: null

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.interval?
            @interval = angular.toJson(
              angular.fromJson(origData['interval']), pretty=true)
          if origData.crontab?
            @crontab = angular.toJson(
              angular.fromJson(origData['crontab']), pretty=true)
          if origData.scenarios?
            @scenarios = angular.toJson(
              angular.fromJson(origData['scenarios']), pretty=true)
          if @interval != {}
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