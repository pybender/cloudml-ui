'use strict'

### Schedule specific Controllers ###

angular.module('app.schedules.controllers', ['app.config', ])

.controller('SchedulesListCtrl', [
  '$scope'
  '$rootScope'
  'Schedule'

($scope, $rootScope, Schedule) ->
  $scope.load = () ->
    Schedule.$loadAll(
      show: ['name','type','created_on','updated_on','enabled',
             'created_by','updated_by'].join(',')
    ).then ((opts) ->
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading schedules')
    )

  $scope.load()

  $rootScope.$on('updateList', () ->
    $scope.load()
  )
])

.controller('ScheduleActionsCtrl', [
  '$scope'
  'Schedule'

($scope, $rootScope, Schedule) ->
  $scope.changeEnabled = (schedule) ->
    if schedule.enabled
      schedule.enabled = false
    else
      schedule.enabled = true
    schedule.$save().then (->
      $scope.$emit('updateList', [])
    ), ((opts) ->
      $scope.setError(opts, 'updating periodic task schedule')
      $scope.$emit('updateList', [])
    )

  $scope.delete_schedule = (schedule) ->
    $scope.openDialog($scope, {
        model: schedule
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete schedule'
        path: schedule.BASE_UI_URL
    })
])

.controller('ScheduleDetailsCtrl', [
  '$scope'
  '$rootScope'
  '$routeParams'
  'Schedule'

($scope, $rootScope, $routeParams, Schedule) ->
  if not $routeParams.id then err = "Can't initialize without schedule id"
  $scope.schedule = new Schedule({id: $routeParams.id})
  $scope.LOADED_SECTIONS = []

  $scope.schedule.$load(
    show: ['name','type','created_on','updated_on','enabled','description',
           'scenario','schedule','created_by'].join(',')
    ).then (->), ((opts)-> $scope.setError(opts, 'loading periodic task schedule'))

  $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        fields = ['name','type','created_on','updated_on','enabled','description',
                 'scenario','schedule','created_by'].join(',')

      if fields isnt ''
        $scope.schedule.$load
            show: fields
        .then ->
          $scope.LOADED_SECTIONS.push mainSection
        , (opts) ->
          $scope.setError(opts, 'loading schedule details')

  $scope.initSections($scope.go)
])

.controller('AddScheduleCtrl', [
  '$scope'
  '$location'
  'Schedule'

  ($scope, $location, Schedule) ->
    $scope.model = new Schedule()
    $scope.types = [{name: 'crontab'}, {name: 'interval'}]
    $scope.err = ''
    $scope.new = true

    $scope.loadScheduleFields = (schedule_type) ->
      $scope.model.$loadScheduleParams(schedule_type)
])


