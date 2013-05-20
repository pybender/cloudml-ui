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
  'app.weights.model'
  'app.weights.controllers'
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
      templateUrl: '/partials/compare_models_form.html'
      controller: 'CompareModelsFormCtl'
    })

    .when('/import_handlers', {
      controller: "ImportHandlerListCtrl"
      templateUrl: '/partials/import_handler/list.html'
    })
    .when('/import_handlers/add', {
      controller: "AddImportHandlerCtl"
      templateUrl: '/partials/import_handler/add.html'
    })
    .when('/import_handlers/:id', {
      controller: 'ImportHandlerDetailsCtrl'
      templateUrl: '/partials/import_handler/details.html'
    })

    # Catch all
    .otherwise({redirectTo: '/models'})

  # Without server side support html5 must be disabled.
  $locationProvider.html5Mode(false)
])

App.run(['$rootScope', 'settings', ($rootScope, settings) ->
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
      $rootScope.sse = new EventSource("#{settings.apiUrl}log/?" + params)
    return $rootScope.sse

  $rootScope.setError = (opts, message=null) ->
    if !message?
        message = 'processing request'

    if opts.data
      $rootScope.err = "Error while #{message}: server responded
 with #{opts.status} (#{opts.data.response.error.message or "no message"})."
    else
      $rootScope.err = "Error while #{message}."

])