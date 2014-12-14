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

    prepareContext = (Server, withError=false) ->
      $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue 'an error'
      response = {}
      server = new Server
      servers = [
        id: 1
        name: 'server1'
        is_default: true
        memory_mb: 100*1024*1024
      ,
        id: 2
        name: 'server2'
        is_default: false
        memory_mb: 1*1024*1024
      ]
      response[server.API_FIELDNAME + 's'] = servers
      if not withError
        $httpBackend.expectGET("#{server.BASE_API_URL}?show=name,id,is_default,memory_mb")
        .respond 200, angular.toJson(response)
      else
        $httpBackend.expectGET("#{server.BASE_API_URL}?show=name,id,is_default,memory_mb")
        .respond 400
      createController 'ServersSelectLoader'
      $httpBackend.flush()
      return servers

    expectModeFileListHttpGet = (ModelFile, serverId, files, withError=false)->
      modelFile = new ModelFile()
      response = {}
      response[modelFile.API_FIELDNAME + 's'] = files
      url = ModelFile.$get_api_url {server_id: serverId}

      $httpBackend.expectGET("#{url}?folder=models&server_id=1&show=server_id,folder")
      .respond 200, angular.toJson(response)

    expectModelHttpGet = (Model, modelDict, withError=false)->
      model = new Model()
      response = {}
      response[model.API_FIELDNAME] = modelDict
      if not withError
        $httpBackend.expectGET("#{model.BASE_API_URL}#{modelDict.id}/?show=trainer_size")
        .respond 200, angular.toJson(response)
      else
        $httpBackend.expectGET("#{model.BASE_API_URL}#{modelDict.id}/?show=trainer_size")
        .respond 400

    it 'should load servers scope', inject (Server)->
      servers = prepareContext(Server)
      expect($scope.servers).toEqual servers
      expect($scope.selectedServer).toBe null

      # with error
      prepareContext(Server, true)
      expect($scope.setError).toHaveBeenCalled()
      expect($scope.err).toEqual 'an error'

    it 'should respond to changed server error getting files', inject (Server, Model, ModelFile)->
      servers = prepareContext(Server)

      url = ModelFile.$get_api_url({server_id: 1})
      $httpBackend.expectGET("#{url}?folder=models&server_id=1&show=server_id,folder")
      .respond 400
      $scope.serverChanged 1
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()
      expect($scope.err).toEqual 'an error'
      expect($scope.selectedServer).toEqual servers[0]

    it 'should respond to changed server and handle errors retrieving models details',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server)

        expectModeFileListHttpGet ModelFile, 1, [{object_id: 10}, {object_id: 20}]

        # 2 models retrieved one of them fails
        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}, true

        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).toHaveBeenCalled()
        expect($scope.err).toEqual 'an error'
        expect($scope.selectedServer).toEqual servers[0]
        expect($scope.selectedServer.models).toBeUndefined()
        expect($scope.selectedServer.totalTrainers).toBeUndefined()
        expect($scope.selectedServer.memoryStatsLoaded).toBeUndefined()
        expect($scope.selectedServer.modelAlreadyUploaded).toBeUndefined()
        expect($scope.selectedServer.modelWillExceed).toBeUndefined()

    it 'should respond to changed server and current model not in it',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server)

        $scope.model = new Model({id: 30, trainer_size: 10*1024*1024})
        expectModeFileListHttpGet ModelFile, 1, [{object_id: 10}, {object_id: 20}]

        # 2 models retrieved one of them fails
        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}

        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[0].id
        expect($scope.selectedServer.models.length).toEqual 2
        expect($scope.selectedServer.totalTrainers).toEqual 30
        expect($scope.selectedServer.memoryStatsLoaded).toEqual true
        expect($scope.selectedServer.modelAlreadyUploaded).toEqual false
        expect($scope.selectedServer.modelWillExceed).toEqual false


  xdescribe 'FileListCtrl', ->

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
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'file'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete file'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  xdescribe 'ServerListCtrl', ->

    it 'should init scope', inject (Server)->
      createController 'ServerListCtrl', {Server: Server}
      expect($scope.MODEL).toEqual Server
      expect($scope.FIELDS).toEqual 'name,ip,folder'
      expect($scope.ACTION).toEqual 'loading servers'


  xdescribe 'ServerDetailsCtrl', ->

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
