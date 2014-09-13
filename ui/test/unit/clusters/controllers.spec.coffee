describe 'clusters/controllers.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.clusters.models'
    module 'app.clusters.controllers'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $scope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'ClusterListCtrl', ->

    it 'should load clusters', inject (Cluster)->
      response = {}
      cluster = new Cluster
      response[cluster.API_FIELDNAME + 's'] = [
        id: 1
        name: 'cluster1'
      ,
        id: 2
        name: 'cluster2'
      ]
      $httpBackend.expectGET("#{cluster.BASE_API_URL}?show=" +
        ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(','))
      .respond 200, angular.toJson(response)
      createController 'ClusterListCtrl',
        $rootScope: $scope
        Cluster: Cluster
        $location: $location
      $httpBackend.flush()

      expect($scope.host).toEqual 'server'
      expect($scope.objects.length).toBe 2
      expect($scope.objects[0].id).toBe 1
      expect($scope.objects[0].name).toEqual 'cluster1'
      expect($scope.objects[1].id).toBe 2
      expect($scope.objects[1].name).toEqual 'cluster2'

      # with error
      $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue 'an error'
      $httpBackend.expectGET("#{cluster.BASE_API_URL}?show=" +
        ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(','))
      .respond 400
      createController 'ClusterListCtrl',
        $rootScope: $scope
        Cluster: Cluster
        $location: $location
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()

      # event updateList triggers a load
      $scope.load = jasmine.createSpy '$scope.load'
      $scope.$emit 'updateList'
      expect($scope.load).toHaveBeenCalled()


  describe 'SshTunnelCtrl', ->

    it 'should create ssh tunnel and check tunnel status, then terminate', inject (Cluster)->
      cluster = new Cluster {id:1, name: 'cluster1'}
      $scope.resetError = jasmine.createSpy '$scope.resetError'
      $scope.$close = jasmine.createSpy '$scope.$close'
      createController 'SshTunnelCtrl',
        openOptions:
          model: cluster
        Cluster: Cluster
        $location: $location
        $timeout: $timeout

      expect($scope.cluster).toEqual cluster
      expect($scope.host).toEqual 'server'
      expect($scope.resetError).toHaveBeenCalled()

      response = {}
      response[cluster.API_FIELDNAME ] = cluster

      $httpBackend.expectPUT("#{cluster.BASE_API_URL}#{cluster.id}/action/create_tunnel/")
      .respond 200, angular.toJson(response)
      $scope.create()
      $httpBackend.flush()

      expect($scope.$close).toHaveBeenCalledWith(true)
      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.timer).toBeDefined()

      # timeout has passed $scope.checkTunnelStatus
      cluster.active_tunnel = -1
      $httpBackend.expectGET("#{cluster.BASE_API_URL}#{cluster.id}/?show=active_tunnel")
      .respond 200, angular.toJson(response)
      $timeout.flush()
      $httpBackend.flush()

      expect($scope.timer).toBeDefined()

      # timeout has passed, tunnel is now active
      cluster.active_tunnel = 1
      $httpBackend.expectGET("#{cluster.BASE_API_URL}#{cluster.id}/?show=active_tunnel")
      .respond 200, angular.toJson(response)
      $timeout.flush()
      $httpBackend.flush()

      expect($scope.timer).toBe null

      # timeout has passed nothing happens
      $timeout.flush()

      # terminate
      $httpBackend.expectPUT("#{cluster.BASE_API_URL}#{cluster.id}/action/terminate_tunnel/")
      .respond 200, angular.toJson(response)

      $scope.terminate()
      $httpBackend.flush()
      expect($scope.$close).toHaveBeenCalledWith(true)
      expect($scope.resetError).toHaveBeenCalled()

    it 'should handle errors in create and check tunnel status', inject (Cluster)->
      cluster = new Cluster {id:1, name: 'cluster1'}
      $scope.resetError = jasmine.createSpy '$scope.resetError'
      $scope.$close = jasmine.createSpy '$scope.$close'
      createController 'SshTunnelCtrl',
        openOptions:
          model: cluster
        Cluster: Cluster
        $location: $location
        $timeout: $timeout

      expect($scope.cluster).toEqual cluster
      expect($scope.host).toEqual 'server'
      expect($scope.resetError).toHaveBeenCalled()

      $scope.setError = jasmine.createSpy '$scope.setError'
      $httpBackend.expectPUT("#{cluster.BASE_API_URL}#{cluster.id}/action/create_tunnel/")
      .respond 400
      $scope.create()
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()

      # check status error
      $httpBackend.expectGET("#{cluster.BASE_API_URL}#{cluster.id}/?show=active_tunnel")
      .respond 400
      $scope.checkTunnelStatus()
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()

      # terminate error
      $httpBackend.expectPUT("#{cluster.BASE_API_URL}#{cluster.id}/action/terminate_tunnel/")
      .respond 400
      $scope.terminate()
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()

    it 'should cancel timer on $scope $destroy', inject (Cluster)->
      cluster = new Cluster {id:1, name: 'cluster1'}
      $scope.resetError = jasmine.createSpy '$scope.resetError'
      $scope.$close = jasmine.createSpy '$scope.$close'
      createController 'SshTunnelCtrl',
        openOptions:
          model: cluster
        Cluster: Cluster
        $location: $location
        $timeout: $timeout

      expect($scope.cluster).toEqual cluster
      expect($scope.host).toEqual 'server'
      expect($scope.resetError).toHaveBeenCalled()

      response = {}
      response[cluster.API_FIELDNAME ] = cluster

      timeoutCalled = false
      $httpBackend.expectPUT("#{cluster.BASE_API_URL}#{cluster.id}/action/create_tunnel/")
      .respond 200, angular.toJson(response)
      $scope.checkTunnelStatus = ->
        timeoutCalled = true
      $scope.create()
      $httpBackend.flush()
      expect($scope.timer).toBeDefined()

      $scope.$emit '$destroy'
      $scope.$digest()
      $timeout.flush()

      expect($scope.timer).toBe null
      expect(timeoutCalled).toBe false


  describe 'ClusterActionsCtrl', ->

    it 'should call unto to open dialogs', inject (Cluster)->
      cluster = new Cluster {id:1, name: 'cluster1'}
      createController 'ClusterActionsCtrl'
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'

      $scope.createSshTunnel(cluster)
      expect($scope.openDialog).toHaveBeenCalledWith
        model: cluster
        template: 'partials/clusters/create_ssh_tunnel.html'
        ctrlName: 'SshTunnelCtrl'

      $scope.terminateSshTunnel(cluster)
      expect($scope.openDialog).toHaveBeenCalledWith
        model: cluster
        template: 'partials/clusters/terminate_ssh_tunnel.html'
        ctrlName: 'SshTunnelCtrl'

      $scope.terminateCluster(cluster)
      expect($scope.openDialog).toHaveBeenCalledWith
        model: cluster
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete cluster'

  describe 'ClusterDetailsCtrl', ->

    it 'should init scope and loaod cluster', inject (Cluster)->
      response = {}
      cluster = new Cluster {id: 999, name: 'cluster1'}
      response[cluster.API_FIELDNAME] = cluster
      $httpBackend.expectGET("#{cluster.BASE_API_URL}#{cluster.id}/?show=" +
        ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(','))
      .respond 200, angular.toJson(response)

      createController 'ClusterDetailsCtrl',
        $routeParams: {id: 999}
        $location: $location
        Cluster: Cluster
      $httpBackend.flush()

      expect($scope.cluster.id).toBe 999
      expect($scope.cluster.name).toEqual 'cluster1'
      expect($scope.host).toEqual 'server'

      # should handle errors in loading
      $httpBackend.expectGET("#{cluster.BASE_API_URL}#{cluster.id}/?show=" +
        ['jobflow_id','master_node_dns','port','status','ip','is_default','created_on','created_by','active_tunnel'].join(','))
      .respond 400

      $scope.setError = jasmine.createSpy '$scope.setError'
      createController 'ClusterDetailsCtrl',
        $routeParams: {id: 999}
        $location: $location
        Cluster: Cluster
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()

      # should handle bad routeParams
      expect( ->
        createController 'ClusterDetailsCtrl',
          $routeParams: {}
          $location: $location
          Cluster: Cluster
      ).toThrow new Error("Can't initialize without cluster id")
