'use strict'

angular.module('app.servers.controllers', ['app.config', ])

.controller('BaseServersSelectLoader', [
  '$scope'
  'Server'

  ($scope, Server) ->
    $scope.servers = []

    fields = ['name', 'id', 'is_default', 'memory_mb']
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
        params = {folder: 'models', server_id: serverId, show:'server_id,folder'}
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
    $scope.FIELDS = 'name,ip,folder'
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
      show: 'id,name,ip,folder,created_on,data,memory_mb'
      ).then (->
        $rootScope.$emit('ServerFileListCtrl:server_loaded')
      ), ((opts)-> $scope.setError(opts, 'loading server'))
])
