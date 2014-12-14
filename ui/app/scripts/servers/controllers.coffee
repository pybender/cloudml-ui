'use strict'

angular.module('app.servers.controllers', ['app.config', ])

.controller('ServersSelectLoader', [
  '$scope'
  '$q'
  'Server'
  'Model'
  'ModelFile'

  ($scope, $q, Server, Model, ModelFile) ->
    $scope.servers = []
    $scope.selectedServer = null

    Server.$loadAll(
      show: 'name,id,is_default,memory_mb'
    ).then ((opts) ->
      for server in opts.objects
        $scope.servers.push
          id: server.id
          name: server.name
          is_default: server.is_default
          memory_mb: server.memory_mb
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading servers')
    )

    $scope.serverChanged = (serverId)->
      filter = _.filter($scope.servers, {id: serverId})
      $scope.selectedServer = if filter.length > 0 then filter[0] else null
      if not $scope.selectedServer.memoryStatsLoaded
        promises = []
        models = []
        modelsSize = 0
        params = {folder: 'models', server_id: serverId, show:'server_id,folder'}
        ModelFile.$loadAll(params).then (opts) ->
          for obj in opts.objects
            model = new Model({id: obj.object_id})
            models.push model
            promises.push model.$load({show: 'trainer_size'})
          if models.length <= 0
            $scope.selectedServer.models = models
            $scope.selectedServer.totalTrainers = modelsSize
            $scope.selectedServer.memoryStatsLoaded = true
            $scope.selectedServer.modelAlreadyUploaded = false
            $scope.selectedServer.modelWillExceed = false
          else
            $q.all(promises).then ->
              modelsSize = _.reduce models, (acc, model)->
                return acc + (model.trainer_size or 0)
              , 0
              $scope.selectedServer.modelAlreadyUploaded = $scope.model.id + '' in _.pluck models, 'id'
              $scope.selectedServer.models = models
              $scope.selectedServer.totalTrainers = Number((modelsSize/1024/1024).toFixed(2))
              $scope.selectedServer.memoryStatsLoaded = true
              $scope.selectedServer.modelWillExceed =
                  ($scope.model.trainer_size/1024/1024) +
                  $scope.selectedServer.totalTrainers > $scope.selectedServer.memory_mb
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
      show: 'id,name,ip,folder,created_on,data'
      ).then (->
        $rootScope.$emit('ServerFileListCtrl:server_loaded')
      ), ((opts)-> $scope.setError(opts, 'loading server'))
])
