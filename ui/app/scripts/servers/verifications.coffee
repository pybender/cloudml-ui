'use strict'

angular.module('app.servers.verifications', ['app.config', ])


.constant('EXAMPLES_COUNT',
  10
)

.controller('ServerModelVerificationListCtrl', [
  '$scope'
  'ModelVerification'

  ($scope, ModelVerification) ->
    $scope.MODEL = ModelVerification
    $scope.FIELDS = ModelVerification.MAIN_FIELDS
    $scope.ACTION = 'loading server model verifications'
    $scope.LIST_MODEL_NAME = ModelVerification.LIST_MODEL_NAME

    $scope.add = () ->
      $scope.openDialog($scope, {
        template: 'partials/servers/verification/add.html'
        ctrlName: 'AddServerModelVerificationListCtrl'
        action: 'add model verification'
        path: "servers/verifications"
      })

    $scope.delete = (verification) ->
      $scope.openDialog($scope, {
        model: verification
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete server model verification'
        path: verification.BASE_UI_URL
      })
])


.controller('AddServerModelVerificationListCtrl', [
  '$scope'
  '$q'
  'ModelVerification'
  'Server'
  'ModelFile'
  'ImportHandlerFile'
  'TestResult'
  'EXAMPLES_COUNT'

  ($scope, $q, ModelVerification, Server, ModelFile, ImportHandlerFile, TestResult, EXAMPLES_COUNT) ->
    $scope.model = new ModelVerification({'count': EXAMPLES_COUNT})
    $scope.modelsDisabled = true
    $scope.datasDisabled = true

    Server.$loadAll(show: ['name', 'id'].join(','))
    .then $scope.getResponseHandler(
      $scope, {
        name: 'servers'
        objects_key: 'servers'
      })...

    $scope.serverChanged = (serverId) ->
      if !serverId?
        $scope.loadingModels = false
        $scope.modelsDisabled = true
        $scope.serverFiles = []
        return
      $scope.model.description = null
      $scope.loadingModels = true
      Server.$active_models(
        server: serverId
      ).then ((opts) ->
        $scope.serverFiles = opts.objects
        $scope.modelsDisabled = false
        $scope.loadingModels = false
      ), ((opts) ->
        $scope.setError(opts, 'loading models that use import handler')
      )
      # params = {folder: 'models', server_id: serverId, show:'server_id,folder,type'}
      # promiseModel = ModelFile.$loadAll(params).then ((opts) ->
      #   $scope.modelsDisabled = false
      #   $scope.serverModels = opts.objects
      # ), ((opts) ->
      #   $scope.setError(opts, 'loading server models')
      # )
      # params = {folder: 'importhandlers', server_id: serverId, show:'server_id,folder'}
      # promiseImportHandler = ImportHandlerFile.$loadAll(params).then  ((opts) ->
      #   $scope.serverImportHandlers = opts.objects
      # ), ((opts) ->
      #   $scope.setError(opts, 'loading server import handlers')
      # )

      # thenFn = (value) ->
      #   return value

      # $q.all([
      #     promiseModel, 
      #     promiseImportHandler
      # ])
      # .then((values) ->
      #   models, import_handlers = values
      #   return values
      # )

    $scope.modelChanged = (model) ->
      if !model?
        $scope.datas = []
        $scope.datasDisabled = true
        $scope.loadingTests = false
        return
      $scope.model.description = null
      $scope.loadingTests = true
      $scope.datasDisabled = true
      TestResult.$loadAll({
        model_id: $scope.model.model_id,
        show: 'name,examples_fields,examples_count'})
      .then ((opts) ->
        $scope.datas = opts.objects
        for file in $scope.serverFiles
          if file.model? and file.model.id == model
            $scope.model.description = file
            $scope.model.import_handler_id = file.import_handler.id
            $scope.importParams = file.import_handler.import_params

        $scope.loadingTests = false
        $scope.datasDisabled = false
      ), ((opts) ->
        $scope.setError(opts, 'loading model test data')
      )

    $scope.dataChanged = (id) ->
      if !id?
        return
      for data in $scope.datas
        if (data.id == id)
          $scope.dataFields = data.examples_fields
          $scope.model.examples_count = data.examples_count
])


.controller('ServerModelVerificationDetailsCtrl', [
  '$scope'
  '$routeParams'
  'ModelVerification'

  ($scope, $routeParams, ModelVerification, VerificationExample) ->
    if not $routeParams.id then err = "Can't initialize without server model verification id"
    $scope.verification = new ModelVerification({id: $routeParams.id})

    $scope.verification.$load(
      show: ModelVerification.MAIN_FIELDS + ',description,result,params_map,error')

    $scope.goSection = (section) ->
      name = section[0]
      subsection = section[1]

    $scope.initSections($scope.goSection, 'about:details')
])


.controller('VerificationExamplesCtrl', [
  '$scope'
  '$rootScope'
  '$location'
  'Data'
  'Model'
  'VerificationExample'

($scope, $rootScope, $location, Data, Model, VerificationExample) ->
  $scope.filter_opts = $location.search() or {} # Used in ObjectListCtrl.
  $scope.simple_filters = {} # Filters by label and pred_label
  $scope.data_filters = {} # Filters by data_input.* fields
  $scope.loading_state = false
  $scope.sort_by = $scope.filter_opts['sort_by'] or ''
  $scope.asc_order = $scope.filter_opts['order'] != 'desc'
  $scope.keysf = Object.keys
  $scope.per_page = 20

  $scope.init = (verification, extra_params={'action': 'result:details'}) ->
    $scope.extra_params = extra_params
    $scope.verification = verification

    $scope.loadDatas = () ->
      (opts) ->
        filter_opts = opts.filter_opts
        delete opts.filter_opts
        show = 'id,result,example'
        opts = _.extend({show: show}, opts, filter_opts)
        opts.sort_by = $scope.sort_by
        opts.order = if $scope.asc_order then 'asc' else 'desc'
        VerificationExample.$loadAll($scope.verification.id, opts)
        .then (resp) ->
          $scope.loading_state = false
          return resp
        , ->
          $scope.loading_state = false
  
  $scope.sort = (sort_by) ->
    if $scope.sort_by == sort_by
      # Only change ordering
      $scope.asc_order = !$scope.asc_order
    else
      # Change sort by field
      $scope.asc_order = true
      $scope.sort_by = sort_by
    $location.search($scope.getParamsDict())
    @load()

  $scope.filter = () ->
    opts = {}
    $scope.filter_opts = _.extend(opts, $scope.extra_params, $scope.simple_filters,
        $scope.data_filters)
    delete opts['action']
    $scope.filter_opts = opts
    $location.search($scope.getParamsDict())

  $scope.getParamsDict = () ->
    sort_opts = {
      sort_by: $scope.sort_by
      order: if $scope.asc_order then 'asc' else 'desc'
    }
    res = _.extend(sort_opts, $scope.filter_opts)
    delete res['action']
    return res

  $scope.getExampleUrl = (example) ->
    example.objectUrl() + '?' + $.param($scope.getParamsDict())
])

.controller('VerificationParamsMapCtrl', [
  '$scope'
  '$routeParams'
  'openOptions'

  ($scope, $routeParams, openOptions) ->
    $scope.resetError()
    model = openOptions.model
    $scope.verification = model
    $scope.importParams = model.import_handler.import_params
    $scope.dataFields = model.test_result.examples_fields
    $scope.fieldsMap = {}

    $scope.appendFieldMap = (importParam, dataField) ->
      if not importParam? or not dataField?
        return
      $scope.fieldsMap[importParam] = dataField
      $scope.importParams.pop importParam
      $scope.importParam = 1
      $scope.dataField = 1

    $scope.removeField = (param) ->
      delete $scope.fieldsMap[param]
      $scope.importParams.push param

    $scope.getVerificationParamsMap = () ->
      {
        params: angular.toJson($scope.fieldsMap)
      }
])


.controller('VerificationExampleDetailsCtrl', [
  '$scope'
  '$routeParams'
  'VerificationExample'

  ($scope, $routeParams, VerificationExample) ->
    if not $routeParams.verification_id then err = "Can't initialize without server model verification id"
    $scope.example = new VerificationExample({id: $routeParams.id, verification_id: $routeParams.verification_id})

    $scope.example.$load(
      show: VerificationExample.MAIN_FIELDS + ',example')
    .then (opts) ->
        $scope.resultJson = angular.toJson($scope.example.result, true)
      , (opts) ->
        $scope.setError(opts, 'loading verification example details')

    $scope.getPredictVectValue = (name) ->
      data = $scope.example.result.data
      keys = Object.keys(data)
      if keys?
        key = keys[0]
        return data[key][name.replace('->', '.')]
      return undefined

    $scope.getRawDataValue = (name) ->
      title = name.replace('->', '.')
      return $scope.example.result.raw_data[0][title]

    $scope.goSection = (section) ->
      name = section[0]
      subsection = section[1]

    $scope.initSections($scope.goSection, 'about:details')

])

.controller('VerifyModelCtrl', [
  '$scope'
  'openOptions'
  'EXAMPLES_COUNT'

  ($scope, openOptions, EXAMPLES_COUNT) ->
    $scope.resetError()
    $scope.data = {'count': EXAMPLES_COUNT}
    $scope.verification = openOptions.model

    $scope.start = (data) ->
      $scope.verification.$verify({'count': data.count}).then ((resp) ->
        $scope.$close(true)
      ), ((opts) ->
        $scope.setError(opts, 'starting ' + $scope.verification.name + ' verification')
      )
])

.controller('ModelVerificationActionsCtrl', [
  '$scope'
  '$route'

  ($scope, $route) ->
    $scope.init = (opts) ->
      if not opts or not opts.verification
        throw new Error "Please specify model verification"

      $scope.verification = opts.verification

    $scope.verify = () ->
      $scope.openDialog($scope, {
        model: $scope.verification
        template: 'partials/servers/verification/verify_popup.html'
        ctrlName: 'VerifyModelCtrl'
      })

    $scope.delete = () ->
      $scope.openDialog($scope, {
        model: $scope.verification
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete server model verification'
        path: $scope.verification.BASE_UI_URL
      })
])