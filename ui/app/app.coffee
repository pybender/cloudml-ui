'use strict'

# Declare app level module which depends on filters, and services
App = angular.module('app', [
  'ngCookies'
  'ngResource'
  'ngRoute'
  'app.config'
  'app.controllers'
  'app.directives'
  'app.filters'
  'app.helpers'
  'app.services'
  'app.templates'
  'ui.bootstrap'
  'ui.select2'
  'ui.codemirror'

  'app.base'
  'app.models.model'
  'app.models.controllers'
  'app.testresults.model'
  'app.testresults.controllers'
  'app.datas.model'
  'app.datas.controllers'
  'app.reports.model'
  'app.reports.controllers'
  'app.datasources.model'
  'app.datasources.controllers'

  'app.importhandlers.models'
  'app.importhandlers.controllers'
  'app.importhandlers.xml.models'
  'app.importhandlers.xml.controllers.input_parameters'
  'app.importhandlers.xml.controllers.importhandlers'
  'app.importhandlers.xml.controllers.entities'
  'app.importhandlers.xml.controllers.datasources'
  'app.importhandlers.xml.controllers.scripts'
  'app.importhandlers.xml.controllers.predict'

  'app.datasets.model'
  'app.datasets.controllers'
  'app.weights.model'
  'app.weights.controllers'
  'app.awsinstances.model'
  'app.awsinstances.controllers'
  'app.clusters.models'
  'app.clusters.controllers'
  'app.logmessages.model'
  'app.logmessages.controllers'
  'app.login.controllers'
  'app.dashboard.model'
  'app.dashboard.controllers'
  'app.features.models'
  'app.features.controllers'
  'app.features.controllers.classifiers'
  'app.features.controllers.transformers'
  'app.features.controllers.named_types'
  'app.features.controllers.base'
  'app.features.controllers.scalers'
  'app.features.controllers.features'
  'app.servers.model'
  'app.servers.controllers'
  'app.servers.verifications'

  'app.play.controllers'
])

App.config([
  '$routeProvider'
  '$locationProvider'

($routeProvider, $locationProvider, config) ->

  $routeProvider
    .when('/dashboard', {
      controller: "DashboardCtrl"
      templateUrl: 'partials/dashboard.html'
      title: 'Dashboard'
    })
    .when('/models', {
      templateUrl: 'partials/models/model_list.html'
      reloadOnSearch: false
      title: 'Models'
    })
    .when('/models/upload_model', {
      templateUrl: 'partials/models/upload_model.html'
      controller: 'AddModelCtl'
      title: 'Upload Model'
    })
    .when('/models/add_model', {
      templateUrl: 'partials/models/add_model.html'
      controller: 'AddModelCtl'
      title: 'Add Model'
    })
    .when('/models/:id', {
      controller: 'ModelDetailsCtrl'
      templateUrl: 'partials/models/model_details.html'
      reloadOnSearch: false
      title: 'Model Details'
    })
    .when('/models/:model_id/tests', {
      redirectTo: (params, loc) ->
        return 'models/' + params.model_id + '?action=test:list'
    })
    .when('/models/:model_id/tests/:id', {
      controller: 'TestDetailsCtrl'
      templateUrl: 'partials/testresults/test_details.html'
      reloadOnSearch: false
      title: 'Model Test Details'
    })
    .when('/models/:model_id/tests/:test_id/grouped_examples', {
      controller: 'GroupedExamplesCtrl'
      templateUrl: 'partials/examples/grouped_examples.html'
      title: 'Grouped Examples'
    })
    # TODO: it doesn't work (angular bug?)
    .when('/models/:model_id/tests/:test_id/examples', {
      redirectTo: (params, loc) ->
        return '/models/' + params.model_id + '/tests/' + params.test_id \
        + '?action=examples:list'
    })
    .when('/models/:model_id/tests/:test_id/examples/:id', {
      controller: 'ExampleDetailsCtrl'
      templateUrl: 'partials/examples/example_details.html'
      title: 'Test Example Details'
    })
    .when('/compare_models', {
      templateUrl: 'partials/reports/compare_models_form.html'
      controller: 'CompareModelsFormCtl'
      title: 'Compare Models'
    })
    .when('/importhandlers', {
      redirectTo: (params, loc) ->
        return '/importhandlers/xml'
    })
    .when('/importhandlers/xml', {
      controller: "XmlImportHandlerListCtrl"
      templateUrl: 'partials/importhandlers/xml/list.html'
      title: 'Import Handlers'
    })
    .when('/importhandlers/xml/add', {
      controller: "AddXmlImportHandlerCtl"
      templateUrl: 'partials/importhandlers/xml/add.html'
      title: 'Add Import Handler'
    })
    .when('/importhandlers/xml/:id', {
      controller: 'XmlImportHandlerDetailsCtrl'
      templateUrl: 'partials/importhandlers/xml/details.html'
      reloadOnSearch: false
      title: 'Import Handler Details'
    })
    .when('/importhandlers/xml/:handler_id/datasets', {
      redirectTo: (p, loc) ->
        return '/importhandlers/xml/' + p.handler_id + '?action=dataset:list'
    })
    .when('/importhandlers/json', {
      controller: "ImportHandlerListCtrl"
      templateUrl: 'partials/import_handler/list.html'
      title: 'Import Handlers'
    })
    .when('/importhandlers/json/add', {
      controller: "AddImportHandlerCtl"
      templateUrl: 'partials/import_handler/add.html'
      title: 'Add Import Handler'
    })
    .when('/importhandlers/json/:id', {
      controller: 'ImportHandlerDetailsCtrl'
      templateUrl: 'partials/import_handler/details.html'
      reloadOnSearch: false
      title: 'Import Handler Details'
    })
    .when('/importhandlers/json/:id/query/add', {
      controller: 'AddImportHandlerQueryCtrl'
      templateUrl: 'partials/import_handler/add_query.html'
      title: 'Add Query'
    })
    .when('/importhandlers/json/:id/query/:num/items/add', {
      controller: 'AddImportHandlerQueryItemCtrl'
      templateUrl: 'partials/import_handler/add_query_item.html'
      title: 'Add Query Item'
    })
    .when('/importhandlers/json/:handler_id/datasets', {
      redirectTo: (params, loc) ->
        return '/importhandlers/json/' + params.handler_id + '?action=dataset:list'
    })
    .when('/importhandlers/:import_handler_type/:import_handler_id/datasets/:id', {
      controller: 'DataSetDetailsCtrl'
      templateUrl: 'partials/datasets/details.html'
      reloadOnSearch: false
      title: 'Dataset Details'
    })
    .when('/aws', {
      redirectTo: '/aws/instances'
      title: 'AWS Instances'
    })
    .when('/aws/instances', {
      controller: "AwsInstanceListCtrl"
      templateUrl: 'partials/aws_instances/list.html'
      title: 'AWS Instances'
    })
    .when('/aws/instances/add', {
      controller: "AddAwsInstanceCtl"
      templateUrl: 'partials/aws_instances/add.html'
      title: 'Add AWS Instance'
    })
    .when('/aws/instances/:id', {
      controller: 'AwsInstanceDetailsCtrl'
      templateUrl: 'partials/aws_instances/details.html'
      title: 'AWS Instance Details'
    })
    .when('/aws/clusters', {
      controller: "ClusterListCtrl"
      templateUrl: 'partials/clusters/list.html'
      title: 'Clusters'
    })
    .when('/aws/clusters/:id', {
      controller: 'ClusterDetailsCtrl'
      templateUrl: 'partials/clusters/details.html'
      title: 'Cluster Details'
    })
    .when('/predict/servers', {
      controller: "ServerListCtrl"
      templateUrl: 'partials/servers/list.html'
      title: 'Servers'
    })
    .when('/predict/servers/:id', {
      controller: 'ServerDetailsCtrl'
      templateUrl: 'partials/servers/details.html'
      title: 'Server Details'
    })
    .when('/predict/verifications', {
      controller: 'ServerModelVerificationListCtrl'
      templateUrl: 'partials/servers/verification/list.html'
      title: 'Server Model Verifications'
    })
    .when('/predict/verifications/:id', {
      controller: 'ServerModelVerificationDetailsCtrl'
      templateUrl: 'partials/servers/verification/details.html'
      title: 'Server Model Verification'
    })
    .when('/predict/verifications/:verification_id/examples/:id', {
      controller: 'VerificationExampleDetailsCtrl'
      templateUrl: 'partials/servers/verification/example_details.html'
      title: 'Server Model Verification Details'
    })
    .when('/predict/verifications/:verification_id/examples', {
      redirectTo: (params, loc) ->
        return 'predict/verifications/' + params.verification_id + '?action=result:details'
    })

    # auth
    .when('/auth/login', {
      controller: 'LoginCtl'
      templateUrl: 'partials/login/login.html'
      title: 'Login'
    })
    .when('/auth/authenticate', {
      controller: 'AuthCtl'
      templateUrl: 'partials/login/auth.html'
      title: 'Authenticate'
    })
    .when('/auth/callback', {
      controller: 'AuthCallbackCtl'
      templateUrl: 'partials/login/auth.html'
      title: 'Authenticate'
    })

    .when('/models/:model_id/features/:set_id/add', {
      controller: "FeatureEditCtrl"
      templateUrl: 'partials/features/items/edit.html'
      title: 'Add Model Feature'
    })
    .when('/models/:model_id/features/:set_id/edit/:feature_id', {
      controller: "FeatureEditCtrl"
      templateUrl: 'partials/features/items/edit.html'
      title: 'Edit Model Feature'
    })
    .when('/models/:model_id/features', {
      redirectTo: (params, loc) ->
        return 'models/' + params.model_id + '?action=model:details'
    })
    .when('/models/:model_id/features/:set_id', {
      redirectTo: (params, loc) ->
        return 'models/' + params.model_id + '?action=model:details'
    })
    # Feature set list (now used only for debug)
    # .when('/features/sets', {
    #   controller: "FeaturesSetListCtrl"
    #   templateUrl: 'partials/features/sets/list.html'
    #   title: 'Features Sets'
    # })

    # Predefined feature objects
    .when('/predefined', {
      redirectTo: '/predefined/classifiers'
    })
    .when('/predefined/types', {
      controller: "FeatureTypeListCtrl"
      templateUrl: 'partials/features/named_types/list.html'
      title: 'Predefined Feature Types'
    })
    .when('/predefined/classifiers', {
      controller: "ClassifiersListCtrl"
      templateUrl: 'partials/features/classifiers/list.html'
      title: 'Predefined Classifiers'
    })
    .when('/predefined/transformers', {
      controller: "TransformersListCtrl"
      templateUrl: 'partials/features/transformers/list.html'
      title: 'Predefined Transformers'
    })
    .when('/predefined/transformers/:id', {
      controller: "TransformerDetailsCtrl"
      templateUrl: 'partials/features/transformers/details.html'
      title: 'Transformer Details'
    })
    .when('/predefined/scalers', {
      controller: "ScalersListCtrl"
      templateUrl: 'partials/features/scalers/list.html'
      title: 'Predefined Scalers'
    })
    .when('/predefined/datasources', {
      controller: "DataSourceListCtrl"
      templateUrl: 'partials/datasources/list.html'
      title: 'Predefined Datasources'
    })

    # Catch all
    .otherwise({redirectTo: '/models'})

  # Without server side support html5 must be disabled.
  $locationProvider.html5Mode(false)
])

App.run(['$rootScope', '$routeParams', '$location', 'settings', 'auth',
         '$cookieStore', '$modal'
($rootScope, $routeParams, $location, settings, $auth, $cookieStore, $modal) ->
  # TODO: nader20140912, not user anywhere schedule for removal
  # $rootScope.Math = window.Math
  # $rootScope.Object = Object
  $rootScope.loadingCount = 0
  $rootScope.pageTitle = ''
  $rootScope.errorList = {}
  $rootScope.setFieldError = (name, msg='') ->
      $rootScope.errorList[name] = msg

  $rootScope.getResponseHandler = ($scope, opts) ->
    # Returns success and error handlers for methods
    # who called API.
    #
    # $scope - current scope
    # opts  - options:
    #    name - name of the action
    #    requiredFields - fields which API should return
    name = opts.name || 'objects'
    objects_key = opts.objects_key
    [(resp) ->
        if opts.requiredFields?
          # check that all required fields were returned via API
          if _.difference(opts.requiredFields, Object.keys(resp)).length > 0
            $scope.setError({}, 'loading ' + name + ' : not all fields was returned via API')
        for key of resp
          $scope[key] = resp[key]
        if objects_key?
          $scope[objects_key] = resp.objects
    , (err) ->
      $scope.setError(err, 'loading ' + name)
    ]

# TODO: nader20140912, not user anywhere schedule for removal
#  # this will be available to all scope variables
#  $rootScope.includeLibraries = true
#
#  # this method will be available to all scope variables as well
#  $rootScope.include = (libraries) ->
#    scope = this
#    # attach each of the libraries directly to the scope variable
#    for key of libraries
#      scope[key] = getLibrary(key)
#    return scope

# TODO: nader20140912, not user anywhere schedule for removal
#  $rootScope.getEventSource = (params='') ->
#    if not $rootScope.sse?
#      $rootScope.sse = new EventSource("#{settings.logUrl}log/?" + params)
#    return $rootScope.sse

# TODO: nader20140912, not user anywhere schedule for removal
#  $rootScope.getEventSourceTest = (params='') ->
#    if not $rootScope.sse_test?
#      $rootScope.sse_test = new EventSource("#{settings.logUrl}log/?" + params)
#    return $rootScope.sse_test

# TODO: nader20140912, not user anywhere schedule for removal
#  $rootScope.initLogMessages = (channel) ->
#    $rootScope.log_messages = []
#    log_sse = $rootScope.getEventSource(params=channel)
#    handleCallback = (msg) ->
#      $rootScope.$apply(() ->
#        if msg?
#          data = JSON.parse(msg.data)
#          $rootScope.log_messages.push(data['data']['msg']))
#    log_sse.addEventListener('message', handleCallback)

  $rootScope.openDialog = (scope, opts) ->
    ###
    Opens a modal dialog
    param $scope: is the parent scope from which the new dialog scope will inherit
    param opts: modal dialog options that will be passed to the controller with
    name openOptions
    ###
    if not scope
      throw new Error('scope is required')

    if not opts?.template
      throw new Error('template is required')

    return $modal.open
      scope: scope
      templateUrl: opts.template
      controller: opts.ctrlName
      windowClass: opts.cssClass
      resolve:
        openOptions: ->
          return opts

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
      if actionString not in $rootScope.initializedSections
        $rootScope.initializedSections.push actionString

  $rootScope.resetError = ->
    $rootScope.err = ''
    $rootScope.statusCode = null
    $rootScope.errorList = {}

  $rootScope.$on('$routeChangeStart', (next, current) ->
      $rootScope.resetError()
  )

  $rootScope.getSelect2Params = (opts) ->
    opts = opts || {}
    return {
      multiple: opts.multiple || false
      data: opts.choices || []
      allowClear: true
      width: 220

      initSelection: (element, callback) ->
        callback(element.val())

      formatResult: (state) ->
        return state

      formatSelection: (state) ->
        return state

      id: (item) ->
        item

      createSearchChoice: (term, data) ->
        return term
    }

  $rootScope.setError = (opts, message=null) ->
    if !message?
        message = 'processing request'

    if opts.data
      resp = opts.data.response
      if resp? && resp.error
        $rootScope.err = "Error while #{message}: server responded
   with #{opts.status} (#{resp.error.message or "no message"})."
        if opts.data.response?.error?.errors?
          for item in resp.error.errors
              $rootScope.setFieldError(item.name, item.error)
      else  # have no info about the error
        $rootScope.err = "Error while #{message}: server responded
   with #{opts.data.status} (#{opts.data.message or "no message"})."
    else
      $rootScope.err = "Unkown error while #{message}."

    $rootScope.statusCode = opts.status
    if opts.status == 401  # Unauthorized
      $auth.logout()
      $location.path("/auth/login")

    return $rootScope.err

  # Authentication
  $rootScope.$on("$routeChangeStart", (event, next, current) ->
    auth_ctrls = ['LoginCtl', 'AuthCtl', 'AuthCallbackCtl']
    if next.$route
      if not $auth.is_authenticated()
        if next.$route.controller not in auth_ctrls
          $cookieStore.put('redirect_to', $location.url())
          $location.path("/auth/login")
      else
        if next.$route.controller in auth_ctrls
          url = $cookieStore.get('redirect_to')
          if url
            $location.url(url)
          else
            $location.path("/models")
  )

  $rootScope.$on('$routeChangeSuccess', (event, current, previous) ->
    if current.hasOwnProperty('$$route')
      $rootScope.pageTitle = current.$$route.title
  )

])