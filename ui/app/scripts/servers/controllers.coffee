'use strict'

angular.module('app.servers.controllers', ['app.config', ])

.controller('ServersSelectLoader', [
  '$scope'
  'Server'

  ($scope, Server) ->
    $scope.servers = []
    Server.$loadAll(
      show: 'name,id'
    ).then ((opts) ->
      for server in opts.objects
        $scope.servers.push {id: server.id, name: server.name}
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading servers')
    )
])
