'use strict'

angular.module('app.servers.controllers', ['app.config', ])

.controller('ServersSelectLoader', [
  '$scope'
  'Server'

  ($scope, Server) ->
    $scope.servers = []
    Server.$loadAll(
      show: 'name,id,is_default'
    ).then ((opts) ->
      for server in opts.objects
        $scope.servers.push {id: server.id, name: server.name}
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading servers')
    )
])

.controller('FileListCtrl', [
  '$scope'
  '$rootScope'
  '$dialog'
  'ModelFile'
  'ImportHandlerFile'

  ($scope, $rootScope, $dialog, ModelFile, ImportHandlerFile) ->
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
        $rootScope.msg = 'File "' + fileName + '" will be updated at server'
      , (opts) ->
        $scope.setError(opts, 'reloading file on Predict')
      )

    $scope.deleteFile = (file) ->
      $scope.openDialog({
        $dialog: $dialog
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
