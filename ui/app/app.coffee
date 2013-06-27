'use strict'

# Declare app level module which depends on filters, and services
App = angular.module('app', [
  'ui'
  'ngCookies'
  'ngResource'
  'app.config'
  'app.controllers'
  'app.directives'
  'app.filters'
  'app.services'
  'ui.bootstrap'

  'app.base'
  'app.models.model'
  'app.models.controllers'
  'app.testresults.model'
  'app.testresults.controllers'
  'app.datas.model'
  'app.datas.controllers'
  'app.reports.model'
  'app.reports.controllers'
  'app.importhandlers.model'
  'app.importhandlers.controllers'
  'app.datasets.model'
  'app.datasets.controllers'
  'app.weights.model'
  'app.weights.controllers'
  'app.awsinstances.model'
  'app.awsinstances.controllers'
  'app.logmessages.model'
  'app.logmessages.controllers'
])

App.config([
  '$routeProvider'
  '$locationProvider'

($routeProvider, $locationProvider, config) ->

  $routeProvider

    .when('/models', {
      controller: "ModelListCtrl"
      templateUrl: '/partials/models/model_list.html'
    })
    .when('/models/:id', {
      controller: 'ModelDetailsCtrl'
      templateUrl: '/partials/models/model_details.html'
      reloadOnSearch: false
    })
    .when('/models/:model_id/tests/:id', {
      controller: 'TestDetailsCtrl'
      templateUrl: '/partials/testresults/test_details.html'
      reloadOnSearch: false
    })
    .when('/models/:model_id/tests/:test_id/grouped_examples', {
      controller: 'GroupedExamplesCtrl'
      templateUrl: '/partials/examples/grouped_examples.html'
    })
    .when('/models/:model_id/tests/:test_id/examples/:id', {
      controller: 'ExampleDetailsCtrl'
      templateUrl: '/partials/examples/example_details.html'
    })
    .when('/upload_model', {
      templateUrl: '/partials/models/upload_model.html'
      controller: 'UploadModelCtl'
    })
    .when('/add_model', {
      templateUrl: '/partials/models/add_model.html'
      controller: 'AddModelCtl'
    })
    .when('/compare_models', {
      templateUrl: '/partials/reports/compare_models_form.html'
      controller: 'CompareModelsFormCtl'
    })
    .when('/importhandlers', {
      controller: "ImportHandlerListCtrl"
      templateUrl: '/partials/import_handler/list.html'
    })
    .when('/importhandlers/add', {
      controller: "AddImportHandlerCtl"
      templateUrl: '/partials/import_handler/add.html'
    })
    .when('/importhandlers/:id', {
      controller: 'ImportHandlerDetailsCtrl'
      templateUrl: '/partials/import_handler/details.html'
      reloadOnSearch: false
    })
    .when('/importhandlers/:handler_id/datasets/:id', {
      controller: 'DataSetDetailsCtrl'
      templateUrl: '/partials/datasets/details.html'
      reloadOnSearch: false
    })
    .when('/aws/instances', {
      controller: "AwsInstanceListCtrl"
      templateUrl: '/partials/aws_instances/list.html'
    })
    .when('/aws/instances/add', {
      controller: "AddAwsInstanceCtl"
      templateUrl: '/partials/aws_instances/add.html'
    })
    .when('/aws/instances/:id', {
      controller: 'AwsInstanceDetailsCtrl'
      templateUrl: '/partials/aws_instances/details.html'
    })

    # Catch all
    .otherwise({redirectTo: '/models'})

  # Without server side support html5 must be disabled.
  $locationProvider.html5Mode(false)
])

App.run(['$rootScope', '$routeParams', '$location', 'settings',
($rootScope, $routeParams, $location, settings) ->
  $rootScope.Math = window.Math

  # this will be available to all scope variables
  $rootScope.includeLibraries = true

  # this method will be available to all scope variables as well
  $rootScope.include = (libraries) ->
    scope = this
    # attach each of the libraries directly to the scope variable
    for key of libraries
      scope[key] = getLibrary(key)
    return scope

  $rootScope.getEventSource = (params='') ->
    if not $rootScope.sse?
      $rootScope.sse = new EventSource("#{settings.logUrl}log/?" + params)
    return $rootScope.sse

  $rootScope.getEventSourceTest = (params='') ->
    if not $rootScope.sse_test?
      $rootScope.sse_test = new EventSource("#{settings.logUrl}log/?" + params)
    return $rootScope.sse_test

  $rootScope.initLogMessages = (channel) ->
    $rootScope.log_messages = []
    log_sse = $rootScope.getEventSource(params=channel)
    handleCallback = (msg) ->
      $rootScope.$apply(() ->
        if msg?
          data = JSON.parse(msg.data)
          $rootScope.log_messages.push(data['data']['msg']))
    log_sse.addEventListener('message', handleCallback)

  $rootScope.openDialog = ($dialog, model, templete, ctrlName,
                           cssClass='modal', action='', path='#') ->
    d = $dialog.dialog(
      modalFade: false
      dialogClass: cssClass
    )
    d.model = model
    d.action = action
    d.path = path
    d.open(templete, ctrlName)
    return d

  DEFAULT_ACTION = "model:details"

  $rootScope.initSections = (go, defaultAction=DEFAULT_ACTION, simple=false) ->
    $rootScope.action = ($routeParams.action or defaultAction).split ':'
    $rootScope.goSection = go
    $rootScope.goSection $rootScope.action
    $rootScope.isSimpleTabs = simple
    $rootScope.initializedSections = []

  $rootScope.setSection = (action) ->
    $rootScope.action = action
    actionString = action.join(':')
    $location.search(
      if actionString == DEFAULT_ACTION then ""
      else "action=#{actionString}")

    needGo = true
    if $rootScope.isSimpleTabs && actionString in $rootScope.initializedSections
      needGo = false

    if needGo
      $rootScope.goSection action
      $rootScope.initializedSections.push(actionString)

  $rootScope.resetError = ->
    $rootScope.err = ''

  $rootScope.setError = (opts, message=null) ->
    if !message?
        message = 'processing request'

    if opts.data
      $rootScope.err = "Error while #{message}: server responded
 with #{opts.status} (#{opts.data.response.error.message or "no message"})."
    else
      $rootScope.err = "Error while #{message}."
    return $rootScope.err

])