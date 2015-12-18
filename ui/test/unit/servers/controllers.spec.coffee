'use strict'

# jasmine specs for datasets

describe 'servers/controllers.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app'
    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.datasets.model'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.models.model'
    module 'app.servers.model'
    module 'app.servers.controllers'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $rootScope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  beforeEach ->
    $rootScope.setError = jasmine.createSpy '$rootScope.setError'

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()

  $base_url = null
  $server = null

  beforeEach inject (Server) ->
    $server = new Server
    $base_url = $server.BASE_API_URL + "?show="

  getServers = (fields) ->
    servers = [
      id: 1
      name: 'server1'
      is_default: true
      memory_mb : 100
      type: 'Production'
    ,
      id: 2
      name: 'server2'
      is_default: false
      memory_mb : 10
      type: 'Development'
    ]
    servers_list = []
    for server in servers
      item = {}
      for name in fields
        item[name] = server[name]
      servers_list.push item
    return servers_list

  expectServersHttpGet = (fields, withError=false) ->
    url = $base_url + fields.join(',')

    if not withError
      servers_list = getServers(fields)
      resp = {}
      resp[$server.API_FIELDNAME + 's'] = servers_list
      $httpBackend.expectGET(url)
        .respond 200, angular.toJson(resp)
    else
      $httpBackend.expectGET(url)
      .respond 400

  describe 'ServersSelectLoaderForImportHandler', ->

    $fields = null

    beforeEach ->
      $fields = ['name', 'id', 'is_default', 'memory_mb', 'type']

    prepareContext = (Server, XmlImportHandler, withError=false) ->
      expectServersHttpGet($fields, withError)
      createController 'ServersSelectLoaderForImportHandler', {Server: Server}
      $scope.model = new XmlImportHandler({id: 1, name: "handler1"})
      $httpBackend.flush()
      return getServers($fields)

    expectImportHandlerFileListHttpGet = (ImportHandlerFile, serverId, files, withError=false)->
      file = new ImportHandlerFile()
      response = {}
      response[file.API_FIELDNAME + 's'] = files
      url = ImportHandlerFile.$get_api_url {server_id: serverId}

      $httpBackend.expectGET("#{url}?folder=importhandlers&server_id=#{serverId}&show=server_id,folder")
      .respond 200, angular.toJson(response)

    it 'should load servers', inject (Server, XmlImportHandler) ->
      prepareContext Server, XmlImportHandler
      expect($scope.servers.length).toEqual getServers($fields).length

    it 'should servers loading error', inject (Server, XmlImportHandler) ->
      prepareContext Server, XmlImportHandler, true
      expect($scope.setError).toHaveBeenCalled()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading servers'

    it 'should respond that the import handler with same name already exist in the server',
      inject (Server, XmlImportHandler, ImportHandlerFile) ->
        servers = prepareContext Server, XmlImportHandler

        expectImportHandlerFileListHttpGet ImportHandlerFile, 1, [{object_id: 10, object_type: 'xml', name: 'handler1'}]
        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[0].id
        expect(/already exist/.test($scope.error)).toEqual true

  describe 'ServersSelectLoaderForModel', ->

    $fields = null

    beforeEach ->
      $fields = ['name', 'id', 'is_default', 'memory_mb', 'type']

    expectModeFileListHttpGet = (ModelFile, serverId, files, withError=false)->
      modelFile = new ModelFile()
      response = {}
      response[modelFile.API_FIELDNAME + 's'] = files
      url = ModelFile.$get_api_url {server_id: serverId}

      $httpBackend.expectGET("#{url}?folder=models&server_id=#{serverId}&show=server_id,folder,type")
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

    prepareContext = (Server, Model, model=null, withError=false) ->
      $scope.model = if model then model else new Model({id: 9999, name: "the model"})
      expectServersHttpGet($fields, withError)

      if not model
        expectModelHttpGet Model, {id: $scope.model.id, trainer_size: 10*1024*1024}
      createController 'ServersSelectLoaderForModel'
      $httpBackend.flush()
      return getServers($fields)

    it 'should load servers scope', inject (Server, Model)->
      servers = prepareContext(Server, Model)
      expect($scope.servers.length).toEqual servers.length
      expect($scope.selectedServer).toBe null

    it 'should show error message, when bad request while loading servers', inject (Server, Model)->
      prepareContext(Server, Model, null, true)
      expect($scope.setError).toHaveBeenCalled()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading servers'

    it 'should respond to changed server error getting files', inject (Server, Model, ModelFile)->
      servers = prepareContext(Server, Model)

      url = ModelFile.$get_api_url({server_id: 1})
      $httpBackend.expectGET("#{url}?folder=models&server_id=1&show=server_id,folder,type")
      .respond 400
      $scope.serverChanged 1
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading models on server'
      expect($scope.selectedServer.name).toEqual servers[0].name
      expect($scope.selectedServer.id).toEqual servers[0].id

    it 'should respond to changed server and handle errors retrieving models details',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server, Model)

        expectModeFileListHttpGet ModelFile, 1, [{object_id: 10}, {object_id: 20}]

        # 2 models retrieved one of them fails
        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}, true

        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).toHaveBeenCalled()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading the model with id: 20'
        # TODO:
        # expect($scope.selectedServer.id).toEqual servers[0].id
        # expect($scope.selectedServer.models.length).toEqual(2)
        # expect($scope.selectedServer.totalTrainers).toBeUndefined()
        # expect($scope.selectedServer.sizeAfterUpload).toBeUndefined()
        # expect($scope.selectedServer.memoryStatsLoaded).toBeUndefined()
        # expect($scope.selectedServer.modelAlreadyUploaded).toBeUndefined()
        # expect($scope.selectedServer.modelWillExceed).toBeUndefined()

    it 'should respond to changed server and current model not in it',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server, Model, new Model({id: 30, trainer_size: 30*1024*1024}))

        expectModeFileListHttpGet ModelFile, 1, [{object_id: 10}, {object_id: 20}]

        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}

        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[0].id
        expect($scope.selectedServer.models.length).toEqual 2
        # TODO:
        # expect($scope.selectedServer.totalTrainers).toEqual 30
        # expect($scope.selectedServer.sizeAfterUpload).toEqual 60
        # expect($scope.selectedServer.memoryStatsLoaded).toEqual true
        # expect($scope.selectedServer.modelAlreadyUploaded).toEqual false
        # expect($scope.selectedServer.modelWillExceed).toEqual false

    it 'should respond to changed server and current model on it',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server, Model, new Model({id: 30, trainer_size: 10*1024*1024}))

        expectModeFileListHttpGet ModelFile, 2, [{object_id: 10}, {object_id: 20}, {object_id: 30}]

        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}
        expectModelHttpGet Model, {id: 30, trainer_size: 30*1024*1024}

        $scope.serverChanged 2
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[1].id
        expect($scope.selectedServer.models.length).toEqual 3
        # TODO:
        # expect($scope.selectedServer.totalTrainers).toEqual 60
        # expect($scope.selectedServer.sizeAfterUpload).toEqual 60
        # expect($scope.selectedServer.memoryStatsLoaded).toEqual true
        # expect($scope.selectedServer.modelAlreadyUploaded).toEqual true
        # expect($scope.selectedServer.modelWillExceed).toEqual true

    it 'should respond to changed server and empty module list',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server, Model, new Model({id: 30, trainer_size: 10*1024*1024}))

        expectModeFileListHttpGet ModelFile, 2, []

        $scope.serverChanged 2
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[1].id
        expect($scope.selectedServer.models.length).toEqual 0
        expect($scope.selectedServer.totalTrainers).toEqual 0
        expect($scope.selectedServer.sizeAfterUpload).toEqual 10
        expect($scope.selectedServer.memoryStatsLoaded).toEqual true
        expect($scope.selectedServer.modelAlreadyUploaded).toEqual false
        expect($scope.selectedServer.modelWillExceed).toEqual false

    it 'should respond to changed server and empty module list, current module will exceed',
      inject (Server, Model, ModelFile)->
        servers = prepareContext(Server, Model, new Model({id: 30, trainer_size: 100*1024*1024}))

        expectModeFileListHttpGet ModelFile, 2, []

        $scope.serverChanged 2
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[1].id
        expect($scope.selectedServer.models.length).toEqual 0
        expect($scope.selectedServer.totalTrainers).toEqual 0
        expect($scope.selectedServer.sizeAfterUpload).toEqual 100
        expect($scope.selectedServer.memoryStatsLoaded).toEqual true
        expect($scope.selectedServer.modelAlreadyUploaded).toEqual false
        expect($scope.selectedServer.modelWillExceed).toEqual true

    it 'should respond that model with same name already exist in the server',
      inject (Server, Model, ModelFile) ->
        servers = prepareContext(Server, Model, new Model({id: 30, trainer_size: 30*1024*1024, name: "the model"}))

        expectModeFileListHttpGet ModelFile, 1, [{object_id: 10, name: "the model"}, {object_id: 20}]

        expectModelHttpGet Model, {id: 10, trainer_size: 10*1024*1024}
        expectModelHttpGet Model, {id: 20, trainer_size: 20*1024*1024}

        $scope.serverChanged 1
        $httpBackend.flush()

        expect($scope.setError).not.toHaveBeenCalled()
        expect($scope.selectedServer.id).toEqual servers[0].id
        expect($scope.selectedServer.models.length).toEqual 2
        expect(/already exist/.test($scope.error)).toEqual true

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
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'file'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete file'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'ServerListCtrl', ->

    it 'should init scope', inject (Server)->
      createController 'ServerListCtrl', {Server: Server}
      expect($scope.MODEL).toEqual Server
      expect($scope.FIELDS).toEqual 'name,ip,folder,type'
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
      $httpBackend.expectGET("#{server.BASE_API_URL}111/?show=id,name,ip,folder,created_on,data,memory_mb,type")
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
      $httpBackend.expectGET("#{server.BASE_API_URL}111/?show=id,name,ip,folder,created_on,data,memory_mb,type")
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()
