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
    })
    .when('/models/:model_id/tests/:id', {
      controller: 'TestDetailsCtrl'
      templateUrl: '/partials/testresults/test_details.html'
    })
    .when('/models/:model_id/tests/:test_id/examples', {
      controller: 'TestExamplesCtrl'
      templateUrl: '/partials/examples/example_list.html',
      reloadOnSearch: false,
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

  DEFAULT_ACTION = "model:details"

  $rootScope.initSections = (go, defaultAction=DEFAULT_ACTION) ->
    $rootScope.action = ($routeParams.action or defaultAction).split ':'
    $rootScope.goSection = go
    $rootScope.goSection $rootScope.action

  $rootScope.setSection = (action) ->
    $rootScope.action = action
    actionString = action.join(':')
    $location.search(
      if actionString == DEFAULT_ACTION then ""
      else "action=#{actionString}")
    $rootScope.goSection action

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