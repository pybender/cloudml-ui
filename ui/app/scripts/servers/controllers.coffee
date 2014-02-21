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

.controller('ServerFileListCtrl', [
  '$scope'
  'Server'
  '$rootScope'

  ($scope, Server, $rootScope) ->
    $scope.objects = []
    $scope.folder = ''

    $scope.init = (folder) ->
      $scope.folder = folder

    $scope.load = () ->
      $scope.server.$getFiles($scope.folder).then((resp) ->
        $scope.objects = resp.data.list
      )

    $scope.removeFile = (fileName) ->
      if confirm('Remove file "' + fileName + '" from server?')
        path = $scope.folder + '/' + fileName
        $scope.server.$removeFile(path).then((resp) ->
          $scope.load()
        , (opts) ->
          $scope.setError(opts, 'removing file')
        )

    $scope.updateFileAtServer = (fileName) ->
      path = $scope.folder + '/' + fileName
      $scope.server.$updateFileAtServer(path).then((resp) ->
        $rootScope.msg = 'File "' + fileName + '" will be updated at server'
      , (opts) ->
        $scope.setError(opts, 'removing file')
      )

    $rootScope.$on('ServerFileListCtrl:server_loaded',
    (event, name, append=false, extra={}) ->
      $scope.load()
    )

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
