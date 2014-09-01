'use strict'

# jasmine specs for datasets

describe 'servers/controllers.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.datasets.model'
    module 'app.xml_importhandlers.models'
    module 'app.importhandlers.model'
    module 'app.models.model'
    module 'app.servers.model'
    module 'app.servers.controllers'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $scope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'ServersSelectLoader', ->

    it 'should load servers scope', inject (Server)->
      response = {}
      server = new Server
      response[server.API_FIELDNAME + 's'] = [
        id: 1
        name: 'server1'
        is_default: true
      ,
        id: 2
        name: 'server2'
        is_default: false
      ]
      $httpBackend.expectGET("#{server.BASE_API_URL}?show=name,id,is_default")
      .respond 200, angular.toJson(response)
      createController 'ServersSelectLoader', {Server: Server}
      $httpBackend.flush()
      expect($scope.servers).toEqual response[server.API_FIELDNAME + 's']

      # with error
      $scope.setError = jasmine.createSpy('$scope.setError').andReturn 'an error'
      $httpBackend.expectGET("#{server.BASE_API_URL}?show=name,id,is_default")
      .respond 400
      createController 'ServersSelectLoader', {Server: Server}
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()
      expect($scope.err).toEqual 'an error'


  describe 'FileListCtrl', ->

    it 'should init scope', inject (ModelFile, ImportHandlerFile)->
      createController 'FileListCtrl', {ModelFile: ModelFile, ImportHandlerFile: ImportHandlerFile}
      expect($scope.FIELDS).toEqual ''
      expect($scope.ACTION).toBeDefined()

      $scope.init {id: 123321}, 'something'
      expect($scope.server).toEqual {id: 123321}
      expect($scope.folder).toEqual 'something'
      expect($scope.MODEL).toEqual ImportHandlerFile
      expect($scope.kwargs).toEqual {server_id: 123321, folder: 'something'}

      $scope.init {id: 123321}, 'models'
      expect($scope.server).toEqual {id: 123321}
      expect($scope.folder).toEqual 'models'
      expect($scope.MODEL).toEqual ModelFile
      expect($scope.kwargs).toEqual {server_id: 123321, folder: 'models'}

    it 'should reload file', inject (ModelFile, ImportHandlerFile)->
      createController 'FileListCtrl', {ModelFile: ModelFile, ImportHandlerFile: ImportHandlerFile}

      file = new ModelFile {id: 111, server_id: 222, name: 'some file'}
      response = {}
      response[file.API_FIELDNAME] = {}
      $httpBackend.expectPUT("#{ModelFile.$get_api_url(file)}#{file.id}/action/reload/")
      .respond 200, angular.toJson(response)
      $scope.reloadFile file
      $httpBackend.flush()
      expect($scope.msg).toBeDefined()

      # with error
      $scope.setError = jasmine.createSpy '$scope.setError'
      $httpBackend.expectPUT("#{ModelFile.$get_api_url(file)}#{file.id}/action/reload/")
      .respond 400
      $scope.reloadFile file
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()

    it 'should open delete dialog', inject (ModelFile, ImportHandlerFile)->
      createController 'FileListCtrl', {ModelFile: ModelFile, ImportHandlerFile: ImportHandlerFile}
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'

      $scope.deleteFile {some: 'file'}
      expect($scope.openDialog).toHaveBeenCalledWith
        model: {some: 'file'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete file'


  describe 'ServerListCtrl', ->

    it 'should init scope', inject (Server)->
      createController 'ServerListCtrl', {Server: Server}
      expect($scope.MODEL).toEqual Server
      expect($scope.FIELDS).toEqual 'name,ip,folder'
      expect($scope.ACTION).toEqual 'loading servers'


  describe 'ServerDetailsCtrl', ->

    it 'should init scope', inject (Server)->

      $rootScope =
        $emit: jasmine.createSpy '$rootScope.$emit'
      createController 'ServerDetailsCtrl',
        $routeParams: {id: 111}
        Server: Server
        $rootScope: $rootScope
      expect($scope.server.id).toEqual 111

      server = new Server
      response = {}
      response[server.API_FIELDNAME] = {}
      $httpBackend.expectGET("#{server.BASE_API_URL}111/?show=id,name,ip,folder,created_on,data")
      .respond 200, angular.toJson(response)
      $httpBackend.flush()

      expect($rootScope.$emit).toHaveBeenCalledWith 'ServerFileListCtrl:server_loaded'

      # error
      $scope.setError = jasmine.createSpy '$scope.setError'
      createController 'ServerDetailsCtrl',
        $routeParams: {id: 111}
        Server: Server
        $rootScope: $rootScope
      expect($scope.server.id).toEqual 111
      $httpBackend.expectGET("#{server.BASE_API_URL}111/?show=id,name,ip,folder,created_on,data")
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()
