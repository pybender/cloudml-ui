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
  $scope.changeEnabled = (schedule, enabled) ->
    schedule.enabled = enabled
    schedule.$save(only: ['enabled']).then (->
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
  $scope.model = new Schedule({id: $routeParams.id})
  $scope.LOADED_SECTIONS = []

  $scope.model.$load(
    show: ['name','created_on','updated_on','enabled','description',
           'scenarios','interval','crontab','created_by'].join(',')
    ).then (->), ((opts)-> $scope.setError(opts, 'loading periodic task schedule'))

  $scope.model.$getConfiguration()
  .then (opts) ->
    $scope.task_config = opts.data.configuration
  , (opts) ->
    $scope.setError(opts, 'loading tasks configuration')
  $scope.task_types = $scope.model.TASK_TYPES

  $scope.go = (section) ->
    fields = ''
    mainSection = section[0]
    if mainSection not in $scope.LOADED_SECTIONS
      # is not already loaded
      fields = ['name','created_on','updated_on','enabled','description',
                'scenarios','interval','crontab','created_by'].join(',')

    if fields isnt ''
      $scope.model.$load
          show: fields
      .then ->
        $scope.LOADED_SECTIONS.push mainSection
        console.log $scope.model.scenarios
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
    $scope.task_types = $scope.model.TASK_TYPES
    $scope.new = true

    $scope.model.$getConfiguration()
    .then (opts) ->
      $scope.task_config = opts.data.configuration
    , (opts) ->
      $scope.setError(opts, 'loading tasks configuration')

])


.controller('TasksActionsCtrl', [
  '$scope'

  ($scope) ->
    $scope.addTask = (root) ->
      $scope.openDialog($scope, {
          model: root
          template: 'partials/schedules/tasks/form.html'
          ctrlName: 'AddTaskCtrl'
          action: 'Add Task'
      })

    $scope.editTask = (index, task, tasks) ->
      $scope.openDialog($scope, {
          model: task
          index: index
          tasks: tasks
          template: 'partials/schedules/tasks/form.html'
          ctrlName: 'EditTaskCtrl'
          action: 'Edit Task'
      })

    $scope.delTasks = (index, tasks, type) ->
      $scope.openDialog($scope, {
        type: type
        tasks: tasks
        index: index
        template: 'partials/schedules/tasks/del_task.html'
        ctrlName: 'DelTaskCtrl'
        action: 'delete task'
      })

])

.controller('DelTaskCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    if openOptions.type == 'single'
      $scope.title = 'delete single task ' + openOptions.tasks[openOptions.index].tasks[0]
      $scope.description = ''
    else
      $scope.title = 'delete tasks ' + openOptions.type
      $scope.description = 'All tasks and sub-chains will also be deleted.'

    $scope.deleteTask = () ->
      openOptions.tasks.splice(openOptions.index, 1)
      $scope.$close(true)

])

.controller('AddTaskCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.task = {
        type: '',
        task: '',
        kwargs: {},
        callback: '',
        callback_kwargs: {}
    }
    $scope.action = openOptions.action

    $scope.Save = () ->
      res = {
        type: $scope.task.type
      }
      if $scope.task.type == 'single'
        res.tasks = [$scope.task.task.task]
        res.kwargs = $scope.task.kwargs || {}
      else
        res.tasks = []
        if $scope.task.type == 'chord'
          res.callback = $scope.task.callback.task
          res.callback_kwargs = $scope.task.callback_kwargs || {}
      openOptions.model.push res
      $scope.$close(true)
])

.controller('EditTaskCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.action = openOptions.action
    $scope.task = angular.copy(openOptions.model)

    $scope.getTaskByName = (task_name) ->
      for t in $scope.task_config
        if t.task == task_name
          return t

    if $scope.task.type == 'single'
      $scope.task.task = $scope.getTaskByName($scope.task.tasks[0])
    if $scope.task.type == 'chord'
      $scope.task.callback = $scope.getTaskByName($scope.task.callback)


    $scope.Save = () ->
      res = {
        type: $scope.task.type
      }
      res.tasks = openOptions.model.tasks
      if $scope.task.type == 'single'
        res.tasks[0] = $scope.task.task.task
        res.kwargs = $scope.task.kwargs || {}
      else
        if openOptions.model.tasks.length > 0 && typeof(openOptions.model.tasks[0]) == 'string'
          res.tasks.splice(0, 1)
      if $scope.task.type == 'chord'
        res.callback = $scope.task.callback.task
        res.callback_kwargs = $scope.task.callback_kwargs || {}
      openOptions.tasks[openOptions.index] = res

      $scope.$close(true)
])