'use strict'

angular.module('app.clusters.controllers', ['app.config', ])

.controller('ClusterListCtrl', [
  '$scope'
  '$rootScope'
  'Cluster'
  '$location'

($scope, $rootScope, Cluster, $location) ->
  $scope.load = () ->
    $scope.host = $location.host()
    Cluster.$loadAll(
      show: ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(',')
    ).then ((opts) ->
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading Clusters')
    )

  $scope.load()

  $rootScope.$on('updateList', () ->
    $scope.load()
  )
])

.controller('SshTunnelCtrl', [
  '$scope'
  'openOptions'
  '$location'
  '$timeout'

  ($scope, openOptions, $location, $timeout) ->
    $scope.resetError()
    $scope.cluster = openOptions.model
    $scope.host = $location.host()

    $scope.create = (result) ->
      $scope.cluster.$createSshTunnel().then (() ->
        $scope.close()
        $scope.timer = $timeout($scope.checkTunnelStatus, 1000)
      ), ((opts) ->
        $scope.setError(opts, 'creating ssh tunnel')
      )

    $scope.checkTunnelStatus = () ->
      $scope.cluster.$load(show: 'active_tunnel')
      .then (opts) ->
        if $scope.cluster.active_tunnel is -1
          $scope.timer = $timeout($scope.checkTunnelStatus, 1000)
        else
          $scope.timer = null
      , (opts) ->
        $scope.setError(opts, 'loading cluster ssh tunnel details')

    $scope.terminate = (result) ->
      $scope.cluster.$terminateSshTunnel().then (() ->
        $scope.close()
      ), ((opts) ->
        $scope.setError(opts, 'terminate ssh tunnel')
      )

    $scope.close = ->
      $scope.resetError()
      $scope.$close(true)

    $scope.$on("$destroy", (event) ->
      if $scope.timer
        $timeout.cancel($scope.timer)
        $scope.timer = null
    )
])

.controller('ClusterActionsCtrl', [
  '$scope'

  ($scope) ->
    $scope.createSshTunnel = (cluster) ->
      $scope.openDialog($scope, {
        model: cluster
        template: 'partials/clusters/create_ssh_tunnel.html'
        ctrlName: 'SshTunnelCtrl'
      })

    $scope.terminateSshTunnel = (cluster) ->
      $scope.openDialog($scope, {
        model: cluster
        template: 'partials/clusters/terminate_ssh_tunnel.html'
        ctrlName: 'SshTunnelCtrl'
      })

    $scope.terminateCluster = (cluster) ->
      $scope.openDialog($scope, {
        model: cluster
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete cluster'
        path: cluster.BASE_UI_URL
      })
])

.controller('ClusterDetailsCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Cluster'

($scope, $routeParams, $location, Cluster) ->
  if not $routeParams.id? then throw new Error("Can't initialize without cluster id")
  $scope.cluster = new Cluster({id: $routeParams.id})
  $scope.host = $location.host()
  $scope.cluster.$load(
    show: ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(',')
    ).then (->), ((opts)-> $scope.setError(opts, 'loading cluster details'))
])
