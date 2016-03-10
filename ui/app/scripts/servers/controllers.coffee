'use strict'

angular.module('app.servers.controllers', ['app.config', ])

.controller('BaseServersSelectLoader', [
  '$scope'
  'Server'

  ($scope, Server) ->
    $scope.servers = []

    fields = ['name', 'id', 'is_default', 'memory_mb', 'type']
    Server.$loadAll(show: fields.join(','))
    .then $scope.getResponseHandler(
      $scope, {
        name: 'servers'
        objects_key: 'servers'
      })...
])


# Select loader for uploading the import handler
# checks whether import handler's name is not duplicated

.controller('ServersSelectLoaderForImportHandler', [
  '$scope'
  '$controller'
  'ImportHandlerFile'

  ($scope, $controller, ImportHandlerFile) ->
    $scope.error = null
    $scope.selectedServer = null
    $controller('BaseServersSelectLoader', {$scope: $scope})

    $scope.serverChanged = (serverId) ->
      filter = _.filter($scope.servers, {id: serverId})
      $scope.selectedServer = if filter.length > 0 then filter[0] else null
      if $scope.selectedServer? && not $scope.selectedServer.statsLoaded
        params = {folder: 'importhandlers', server_id: serverId, show:'server_id,folder'}
        ImportHandlerFile.$loadAll(params).then (opts) ->
          for obj in opts.objects
            if obj.name == $scope.model.name
              $scope.error = 'Import Handler with name "' + obj.name + '" already exist on the server. Please rename your import handler or delete the import handler from the <a href="#' + $scope.selectedServer.objectUrl() + '" target="_blank">server</a> before uploading.'
        $scope.selectedServer.statsLoaded = true
])

# Select loader for uploading the model
# checks whether it's enough of the memory
# in the server, model's name, etc.

.controller('ServersSelectLoaderForModel', [
  '$scope'
  '$q'
  '$controller'
  'Model'
  'ModelFile'

  ($scope, $q, $controller, Model, ModelFile) ->
    $scope.error = null
    $scope.selectedServer = null
    $controller('BaseServersSelectLoader', {$scope: $scope})

    if not $scope.model.trainer_size
      $scope.model.$load({show: 'trainer_size'})

    $scope.serverChanged = (serverId)->
      filter = _.filter($scope.servers, {id: serverId})
      $scope.selectedServer = if filter.length > 0 then filter[0] else null
      if $scope.selectedServer? && not $scope.selectedServer.memoryStatsLoaded
        promises = []
        models = []
        modelsSize = 0
        params = {folder: 'models', server_id: serverId, show:'server_id,folder,type'}
        ModelFile.$loadAll(params).then (opts) ->
          if opts.objects.length <= 0
            # queue empty promise to consolidate code in $q.all for both cases
            # of no modules on server and many modules on server
            promises.push ->
              return $q (resolve)-> resolve()
          else
            $scope.serverModels = opts.objects
            for obj in opts.objects
              if obj.name == $scope.model.name
                $scope.error = 'Model with name "' + obj.name + '" already exist on the server. Please rename your model or delete the model from the <a href="#' + $scope.selectedServer.objectUrl() + '" target="_blank">server</a> before uploading.'
              model = new Model({id: obj.object_id})
              models.push model
              model.$load({show: 'trainer_size'})
              .then (opts) ->
                promises.push model
              , (opts) ->
                $scope.err = $scope.setError(opts, 'loading the model with id: ' + model.id)

          $q.all(promises).then ->
            modelsSize = _.reduce models, (acc, model)->
              return acc + (model.trainer_size or 0)
            , 0
            $scope.selectedServer.modelAlreadyUploaded =
              _.reduce models, (acc, model)->
                return acc or model.id + '' is $scope.model.id + ''
              , false
            $scope.selectedServer.models = models
            $scope.selectedServer.totalTrainers =
              Number((modelsSize/1024/1024).toFixed(2))
            $scope.selectedServer.sizeAfterUpload =
                $scope.selectedServer.totalTrainers +
                (if $scope.selectedServer.modelAlreadyUploaded then 0 else ($scope.model.trainer_size/1024/1024))
            $scope.selectedServer.modelWillExceed =
                $scope.selectedServer.sizeAfterUpload > $scope.selectedServer.memory_mb
            $scope.selectedServer.memoryStatsLoaded = true
          , (reason)->
            $scope.err = $scope.setError('', 'loading the server models with reason:' + reason)
        , (opts) ->
          $scope.err = $scope.setError(opts, 'loading models on server')
  ])

.controller('FileListCtrl', [
  '$scope'
  '$rootScope'
  'ModelFile'
  'ImportHandlerFile'

  ($scope, $rootScope, ModelFile, ImportHandlerFile) ->
    $scope.FIELDS = ''
    $scope.ACTION = 'loading files info from Amazon S3'

    $scope.init = (server, folder) ->
      $scope.server = server
      $scope.folder = folder
      if folder == 'models'
        $scope.MODEL = ModelFile
      else
        $scope.MODEL = ImportHandlerFile
      $scope.kwargs = {'server_id': server.id, 'folder': folder}

    $scope.reloadFile = (file) ->
      file.$reload().then((resp) ->
        $rootScope.msg = 'File "' + file.name + '" will be updated at server'
      , (opts) ->
        $scope.setError(opts, 'reloading file on Predict')
      )

    $scope.deleteFile = (file) ->
      $scope.openDialog($scope, {
        model: file
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete file'
      })
])

.controller('ServerListCtrl', [
  '$scope'
  'Server'

  ($scope, Server) ->
    $scope.MODEL = Server
    $scope.FIELDS = 'name,ip,folder,type'
    $scope.ACTION = 'loading servers'

])

.controller('ServerDetailsCtrl', [
  '$scope'
  '$routeParams'
  'Server'
  '$rootScope'

  ($scope, $routeParams, Server, $rootScope) ->
    if not $routeParams.id then err = "Can't initialize without instance id"
    $scope.server = new Server({id: $routeParams.id})

    $scope.server.$load(
      show: 'id,name,ip,folder,created_on,data,memory_mb,type'
      ).then (->
        $rootScope.$emit('ServerFileListCtrl:server_loaded')
      ), ((opts)-> $scope.setError(opts, 'loading server'))
])

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
          if file.model.id == model
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
        1
      , (opts) ->
        $scope.setError(opts, 'loading verification example details')

    $scope.getPredictVectValue = (name) ->
      data = $scope.example.result.data
      keys = Object.keys(data)
      if keys?
        key = keys[0]
        return data[key][name.replace('->', '.')]
      return undefined

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