'use strict'

# jasmine specs for datasets

describe 'servers/verifications.coffee', ->

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
    module 'app.servers.verifications'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $rootScope = null
  $location = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  beforeEach ->
    $rootScope.setError = jasmine.createSpy '$rootScope.setError'
    #$rootScope.getResponseHandler = jasmine.createSpy '$rootScope.getResponseHandler'

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()

  $server_base_url = null
  $server = null

  $base_url = null
  $verification = null

  beforeEach inject (Server, ModelVerification) ->
    $verification = new ModelVerification
    $base_url = $verification.BASE_API_URL + "?show="

    $server = new Server({id: 1})
    $server_base_url = $server.BASE_API_URL + "?order=asc&show="

  getServers = () ->
    servers = [
      id: 1
      name: 'server1'
    ,
      id: 2
      name: 'server2'
    ]
    return servers

  expectServersHttpGet = (withError=false) ->
    url = $server_base_url + ['name', 'id'].join(',') + "&sort_by=name"

    if not withError
      servers_list = getServers()
      resp = {}
      resp[$server.API_FIELDNAME + 's'] = servers_list
      $httpBackend.expectGET(url)
        .respond 200, angular.toJson(resp)
    else
      $httpBackend.expectGET(url)
      .respond 400

  getPredictClasses = () ->
    classes = {
      'class1': ['field1', 'field2']
      'class2': ['field12']
      'class3': ['field1', 'field3']
    }
    return classes

  expectPredictClassesHttpGet = (withError=false)->
    response = {}
    response['classes'] = getPredictClasses()
    if not withError
      $httpBackend.expectGET("#{$verification.BASE_API_URL}action/predict_classes/")
      .respond 200, angular.toJson(response)
    else
      $httpBackend.expectGET("#{$verification.BASE_API_URL}action/predict_classes/")
      .respond 400


  describe 'AddServerModelVerificationListCtrl', ->

    prepareContext = (withClassesError, withServerError) ->
      $scope.setError = jasmine.createSpy '$scope.setError'
      expectPredictClassesHttpGet withClassesError
      expectServersHttpGet withServerError
      createController 'AddServerModelVerificationListCtrl'
      $httpBackend.flush()
      return getServers()

    expectServerFilesHttpGet = (serverId, withError=false) ->
      url = "#{$server.BASE_API_URL}action/models/?server=#{serverId}"
      if not withError
        response = {
          files: [
            {
              "model_metadata": "m1"
              "import_handler_name": "h1"
              "import_handler_metadata": {}
              "model": {"id": 11, "import_handler_id": 1}
              "import_handler": {"import_params": ["app_id"], "id": 1}
              "model_name": "m1"
            },
            {
              "import_handler_name": "h2"
              "import_handler": {"import_params": ["my_id"], "id": 2}
              "import_handler_metadata": {}
            }],
          all_model_files: [
            {
              "last_modified": "2015-11-09"
              "id": "id.model"
              "object_id": 11
              "name": "the model"
            },
            {
              "last_modified": "2015-11-09"
              "id": "id.model"
              "object_id": 222
              "name": "the model 2"
            }]
          }
        $httpBackend.expectGET(url)
        .respond 200, angular.toJson(response)
        return response
      else
        $httpBackend.expectGET(url)
        .respond 400

    expectDatasRequest = (modelId, withError) ->
        inject (TestResult) ->
          testResult = new TestResult({id:111, model_id: modelId})
          url = "#{testResult.BASE_API_URL}?model_id=#{modelId}&show=name,examples_fields,examples_count"
          if not withError
            response = {}
            response[testResult.API_FIELDNAME+'s'] = [
              {
                id: 123
                name: "test1"
                examples_fields: ["field1", "field2"]
                examples_count: 99
              }]
            $httpBackend.expectGET(url)
              .respond 200, angular.toJson(response)
          else
            $httpBackend.expectGET(url)
            .respond 400

    selectServer = (serverId) ->
      $scope.model.server_id = serverId
      serverFilesResp = expectServerFilesHttpGet(serverId)
      $scope.loadServerFiles serverId
      $httpBackend.flush()
      expect($scope.serverFiles.length).toEqual serverFilesResp['files'].length
      expect($scope.datas).toEqual []
      expect($scope.dataFields).toEqual []

    selectImportHandler = (importHandlerId, modelId, predefined=true) ->
      expectDatasRequest(modelId)
      if predefined
        $scope.model.import_handler_id = importHandlerId
        $scope.importHandlerChanged importHandlerId
      else
        $scope.model.import_handler_id = importHandlerId
        $scope.importHandlerChanged importHandlerId
        $scope.model.model_id = modelId
        $scope.loadDatas modelId
      $httpBackend.flush()


    describe 'Form Initialization', ->

      it 'should init scope, load servers, predict classes and watch for params_map changes', ->
        prepareContext false, false
        expect($scope.model.count).toEqual 0
        expect($scope.serverFiles).toEqual []
        expect($scope.datas).toEqual []
        expect($scope.importParams).toEqual []
        expect($scope.dataFields).toEqual []
        expect($scope.verifyAllowed).toBe false

        classes = getPredictClasses()
        classes['- Other -'] = []
        expect($scope.predictClassesConfig).toEqual classes

        servers = getServers()
        expect($scope.servers[0].id).toEqual servers[0].id
        expect($scope.servers[1].id).toEqual servers[1].id
        expect($scope.servers[0].name).toEqual servers[0].name
        expect($scope.servers[1].name).toEqual servers[1].name

        # check verify allowed
        $scope.model.params_map = '{"field1": "field11"}'
        $scope.$digest()
        expect($scope.verifyAllowed).toBe true

        $scope.model.params_map = {}
        $scope.$digest()
        expect($scope.verifyAllowed).toBe false

        $scope.model.params_map = '{}'
        $scope.$digest()
        expect($scope.verifyAllowed).toBe false


      it 'should set error on predict classes loading failure', ->
        prepareContext true, false
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading types and parameters'


      it 'should set error on server loading failure', ->
        prepareContext false, true
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading servers'


    describe 'Server Select', ->
      beforeEach ->
        prepareContext false, false

      it 'do nothing when no server selected', ->
        $scope.loadServerFiles
        expect($scope.serverFiles).toEqual []
        expect($scope.datas).toEqual []
        expect($scope.dataFields).toEqual []

      it 'force server files loading when server selected', ->
        selectServer(1)

      it 'show error while loading server files when we have 400 resp', ->
        serverId = 1
        expectServerFilesHttpGet(serverId, true)
        $scope.loadServerFiles serverId
        $httpBackend.flush()
        expect($scope.serverFiles).toEqual []
        expect($scope.datas).toEqual []
        expect($scope.dataFields).toEqual []
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading models that use import handler'

    describe 'Import Handler/Model Select', ->
      beforeEach ->
        prepareContext false, false
        selectServer(1)

      it 'should load datas (import handler with predefined model)', ->
        importHandlerId = 1
        # model id of this import handler is 11
        expectDatasRequest(11)
        $scope.model.import_handler_id = importHandlerId
        $scope.importHandlerChanged importHandlerId
        expect($scope.showModelSelect).toEqual false
        expect($scope.datas).toEqual []
        expect($scope.dataFields).toEqual []
        $httpBackend.flush()

        expect($scope.datas[0].id).toEqual 123
        expect($scope.datas[0].name).toEqual "test1"
        expect($scope.datas[0].examples_fields).toEqual ["field1", "field2"]
        expect($scope.datas[0].examples_count).toEqual 99
        expect($scope.dataFields).toEqual []
        expect($scope.model.description).toEqual $scope.serverFiles[0]
        expect($scope.model.import_handler_id).toEqual importHandlerId
        expect($scope.predictClassesConfig['- Other -']).toEqual ["app_id"]
        expect($scope.importHandlerParams).toEqual ["app_id"]

      it 'should load datas (import handler with model defined via script -> system should ask user to select the model manually)', ->
        # selecting import handler
        importHandlerId = 2  # model is not spec in the import handler
        $scope.model.import_handler_id = importHandlerId
        $scope.importHandlerChanged importHandlerId

        expect($scope.datas).toEqual []
        expect($scope.dataFields).toEqual []
        expect($scope.showModelSelect).toEqual true
        expect($scope.model.model_id).toBeNull()
        
        # selecting the model
        $scope.model.model_id = 222
        $scope.loadDatas 222
        expectDatasRequest(222)
        $httpBackend.flush()

        expect($scope.datas[0].id).toEqual 123
        expect($scope.datas[0].name).toEqual "test1"
        expect($scope.datas[0].examples_fields).toEqual ["field1", "field2"]
        expect($scope.datas[0].examples_count).toEqual 99
        expect($scope.dataFields).toEqual []
        expect($scope.model.description).toEqual $scope.serverFiles[1]
        expect($scope.model.import_handler_id).toEqual importHandlerId
        expect($scope.predictClassesConfig['- Other -']).toEqual ["my_id"]
        expect($scope.importHandlerParams).toEqual ["my_id"]


      it 'process 400 error (loading datas), when selecting import handler/model', ->
        importHandlerId = 1
        # model id of this import handler is 11
        expectDatasRequest(11, true)
        $scope.model.import_handler_id = importHandlerId
        $scope.importHandlerChanged importHandlerId
        $httpBackend.flush()
        expect($scope.datas).toEqual []
        expect($scope.dataFields).toEqual []
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading model test data'

    describe 'Test Data Select', ->
      beforeEach ->
        prepareContext false, false
        selectServer(1)
        selectImportHandler(1, 11)  # in the import handler 1 model is 11.

      it 'should load test data fields, when selecting the TestResult.', ->
        $scope.loadFields
        expect($scope.dataFields).toEqual []

        $scope.loadFields 122
        expect($scope.dataFields).toEqual []

        $scope.loadFields 123
        expect($scope.dataFields).toEqual ["field1", "field2"]
        expect($scope.model.examples_count).toEqual 99
        expect($scope.model.count).toEqual 10

    describe 'Predict Class Select', ->
      beforeEach ->
        prepareContext false, false
        selectServer(1)
        selectImportHandler(1, 11)  # in the import handler 1 model is 11.
        testResultId = 123
        $scope.loadFields testResultId

      it 'should load import params for clazz', ->
        prepareContext false, false

        $scope.loadIParams "some"
        expect($scope.clazz).toEqual "some"
        expect($scope.importParams).toEqual []

        $scope.loadIParams "class2"
        expect($scope.clazz).toEqual "class2"
        expect($scope.importParams).toEqual ["field12"]


      it 'should reset data and set class', ->
        prepareContext false, false
        $scope.clazz = "class2"

        $scope.resetData ["serverFiles", "datas"]
        expect($scope.datas).toEqual []
        expect($scope.serverFiles).toEqual []
        expect($scope.model.test_result_id).toEqual ''
        expect($scope.model.model_id).toEqual ''
        expect($scope.model.examples_count).toEqual 0
        expect($scope.model.count).toEqual 0
        expect($scope.importParams).toEqual ["field12"]


  describe 'ModelVerificationActionsCtrl', ->

    it "should init controller, make no request", inject (ModelVerification) ->
      createController "ModelVerificationActionsCtrl"
      $scope.init {verification: new ModelVerification({id:123})}

      expect($scope.verification.id).toEqual 123


    it "should open delete dialog", inject (ModelVerification) ->
      $scope.verification = new ModelVerification {id: 4321}
      $scope.openDialog = jasmine.createSpy('$scope.openDialog')

      createController "ModelVerificationActionsCtrl"
      $scope.delete()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: $scope.verification
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete server model verification'
        path: $scope.verification.BASE_UI_URL
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


    it "should open verify dialog", inject (ModelVerification) ->
      $scope.verification = new ModelVerification {id: 4321}
      $scope.openDialog = jasmine.createSpy('$scope.openDialog')

      createController "ModelVerificationActionsCtrl"
      $scope.verify()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: $scope.verification
        template: 'partials/servers/verification/verify_popup.html'
        ctrlName: 'VerifyModelCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'VerifyModelCtrl', ->

    it 'should init scope, start verification', inject (ModelVerification)->

      expect ->
        createController 'VerifyModelCtrl',
          $scope: $scope
          openOptions: {}
          count: 10
        .toThrow new Error 'Please specify model verification'

      model = new ModelVerification
        id: 999
        name: 'someModelVerification'
      openOptions = {model: model}
      $scope.resetError = jasmine.createSpy '$scope.resetError'
      $scope.$close = jasmine.createSpy '$scope.$close'
      $scope.setError = jasmine.createSpy '$scope.setError'

      createController 'VerifyModelCtrl', {$scope: $scope, openOptions: openOptions, 10}

      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.verification.id).toEqual openOptions.model.id
      expect($scope.verification.name).toEqual openOptions.model.name
      expect($scope.data).toEqual {'count': 10}

      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/verify/"
      .respond 200, angular.toJson(response)
      $scope.start {count:15}
      $httpBackend.flush()
      expect($scope.$close).toHaveBeenCalled()

      # error saving the model
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/verify/"
      .respond 400
      $scope.start {count:15}
      $httpBackend.flush()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'starting someModelVerification verification'


  describe 'ServerModelVerificationListCtrl', ->

    it 'should init scope', inject (ModelVerification)->
      createController 'ServerModelVerificationListCtrl', {ModelVerification: ModelVerification}
      expect($scope.MODEL).toEqual ModelVerification
      expect($scope.FIELDS).toEqual 'id,model,server,test_result,created_by,created_on,import_handler,status,clazz'
      expect($scope.ACTION).toEqual 'loading server model verifications'

    it 'should open delete dialog', inject (ModelVerification)->
      createController 'ServerModelVerificationListCtrl', {ModelVerification: ModelVerification}
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'

      $scope.delete {some: 'verification'}
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'verification'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete server model verification'
        path: ModelVerification.BASE_UI_URL
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should open add verification dialog', inject (ModelVerification)->
      createController 'ServerModelVerificationListCtrl', {ModelVerification: ModelVerification}
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'

      $scope.add()
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        template: 'partials/servers/verification/add.html'
        ctrlName: 'AddServerModelVerificationListCtrl'
        action: 'add model verification'
        path: "servers/verifications"
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'ServerModelVerificationDetailsCtrl', ->

    it  'should throw exception if no routeParams.id',
      inject (ModelVerification)->
        expect ->
          createController 'ServerModelVerificationDetailsCtrl',
            $routeParams: {}
            ModelVerification: ModelVerification
        .toThrow new Error 'Can\'t initialize without server model verification id'

    it 'should init scope', inject (ModelVerification)->
      $scope.initSections = jasmine.createSpy '$scope.initSections'

      createController 'ServerModelVerificationDetailsCtrl',
        $routeParams: {id: 111}
        ModelVerification: ModelVerification
        $rootScope: $rootScope
      expect($scope.verification.id).toEqual 111

      verification = new ModelVerification
      response = {}
      response[verification.API_FIELDNAME] = {}
      $httpBackend.expectGET("#{verification.BASE_API_URL}111/?show=id,model,server,test_result,created_by,created_on,import_handler,status,clazz,description,result,params_map,error")
      .respond 200, angular.toJson(response)
      $httpBackend.flush()

      expect($scope.initSections).toHaveBeenCalledWith $scope.goSection, 'about:details'

      # error
      $scope.setError = jasmine.createSpy '$scope.setError'
      createController 'ServerModelVerificationDetailsCtrl',
        $routeParams: {id: 111}
        ModelVerification: ModelVerification
        $rootScope: $rootScope
      expect($scope.verification.id).toEqual 111
      $httpBackend.expectGET("#{verification.BASE_API_URL}111/?show=id,model,server,test_result,created_by,created_on,import_handler,status,clazz,description,result,params_map,error")
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()


  describe 'VerificationExamplesCtrl', ->

    $data_fields_url = null
    $data_fields_response = {"fields": ["data_input->total", "data_input->country"]}

    it 'should load an initialize scope with default values', ->
      createController 'VerificationExamplesCtrl'
      expect($scope.filter_opts).toBeDefined()
      expect($scope.simple_filters).toEqual {}
      expect($scope.data_filters).toEqual {}
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true
      expect($scope.loading_state).toBe false


    it 'should load an initialize scope with values from query string', ->
      $location.search({sort_by: 'the_field', order: 'desc'})
      createController 'VerificationExamplesCtrl'
      expect($scope.filter_opts).toEqual {sort_by: 'the_field', order: 'desc'}
      expect($scope.simple_filters).toEqual {}
      expect($scope.data_filters).toEqual {}
      expect($scope.sort_by).toEqual 'the_field'
      expect($scope.asc_order).toBe false


    it 'should init scope', inject (ModelVerification) ->

      verification = new ModelVerification({id:333})

      createController 'VerificationExamplesCtrl'
      $scope.init verification, {'param': 'param1'}
      expect($scope.verification.id).toEqual 333
      expect($scope.extra_params).toEqual {'param': 'param1'}


    it 'should load data with and without filter options', inject (ModelVerification, VerificationExample)->
      verification = new ModelVerification({id:333})

      createController 'VerificationExamplesCtrl'
      $scope.init verification
      $scope.loadDatas()({})

      d1 = new VerificationExample {id: 777, verification_id: verification.id}
      d2 = new VerificationExample {id: 778, verification_id: verification.id}
      response = {}
      response[d1.API_FIELDNAME + 's'] = [d1, d2]
      $httpBackend.expectGET "#{d1.BASE_API_URL}?order=asc&show=id,result,example&sort_by="
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.loading_state).toBe false

      # with some filter options
      $scope.sort_by = 'sortby_zinger'
      $scope.asc_order = false
      $scope.loadDatas()({filter_opts: 'filter_opts', option1: 'option1'})
      $httpBackend.expectGET "#{d1.BASE_API_URL}?option1=option1&order=desc&show=id,result,example&sort_by=sortby_zinger"
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.loading_state).toBe false

      # handling errors
      $scope.sort_by = ''
      $scope.asc_order = true
      $scope.loadDatas()({})
      $httpBackend.expectGET "#{d1.BASE_API_URL}?order=asc&show=id,result,example&sort_by="
      .respond 400
      $httpBackend.flush()

      expect($scope.loading_state).toBe false


    it 'should change sort configuration', ->
      createController 'VerificationExamplesCtrl'

      $scope.load = jasmine.createSpy '$scope.load'

      # switching sort order
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual {}
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe false
      expect($location.search()).toEqual { sort_by : '', order : 'desc' }
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual { sort_by : '', order : 'asc' }

      # changing sort_by, but first let's reset
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe false
      expect($location.search()).toEqual { sort_by : '', order : 'desc' }
      $scope.sort('zinger')
      expect($scope.sort_by).toEqual 'zinger'
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual { sort_by : 'zinger', order : 'asc' }


    it 'should change query string when init data filters', ->
      createController 'VerificationExamplesCtrl'
      data_filters =
        "data_input->country" : 'Australia'
        "data_input->total" : 10

      $scope.data_filters = data_filters
      $scope.filter()

      expect($scope.filter_opts).toEqual data_filters
      expect($location.search()).toEqual _.extend(data_filters, {sort_by : '', order: 'asc'})


    it 'should build parameters dict', ->

      createController 'VerificationExamplesCtrl'
      expect($scope.getParamsDict()).toEqual {sort_by : '', order: 'asc'}

      $scope.filter_opts = {filter1_name: 'filter1_value', action: 'some_action'}
      $scope.sort_by = 'some-field'
      $scope.asc_order = false
      expect($scope.getParamsDict()).toEqual {sort_by: 'some-field', order: 'desc', filter1_name: 'filter1_value'}


    it 'should build example url', inject (VerificationExample)->
      createController 'VerificationExamplesCtrl'

      d = new VerificationExample {id:999, verification_id: 777}
      expect($scope.getExampleUrl d).toEqual '/predict/verifications/777/examples/999?sort_by=&order=asc'


  describe 'VerificationExampleDetailsCtrl', ->

    it  'should throw exception if no routeParams.id',
      inject (VerificationExample)->
        expect ->
          createController 'VerificationExampleDetailsCtrl',
            VerificationExample: VerificationExample
            $routeParams: {}
        .toThrow new Error 'Can\'t initialize without server model verification id'


    it 'should initialize scope and call goSection', inject (VerificationExample)->
      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      $routeParams = {id: 888, verification_id: 777}
      d1 = new VerificationExample({id: 888, verification_id: 777, result: 'some_result'})

      createController 'VerificationExampleDetailsCtrl',
        $routeParams: $routeParams
        VerificationExample: VerificationExample

      expect($scope.example.id).toEqual 888

      fields = ['id', 'example', 'result', 'example'].join(',')
      url = d1.BASE_API_URL + "#{d1.id}/?show=" + fields

      # error in http
      $httpBackend.expectGET url
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading verification example details'

      createController 'VerificationExampleDetailsCtrl',
        $routeParams: $routeParams
        VerificationExample: VerificationExample
      response = {}
      response[d1.API_FIELDNAME] = d1
      $httpBackend.expectGET url
      .respond 200, angular.toJson response
      $httpBackend.flush()
      expect($scope.resultJson).toEqual '"some_result"'
      expect($scope.initSections).toHaveBeenCalledWith $scope.goSection, 'about:details'


    it 'should return Predict Vect Value', inject (VerificationExample)->
      $routeParams = {id: 888, verification_id: 777}
      d1 = new VerificationExample({id: 888, verification_id: 777, result: {data: {'data1': {'nnn.1': 'v1'}, 'data2': {'nnn.2': 'mmm'}}}})
      createController 'VerificationExampleDetailsCtrl',
        $routeParams: $routeParams
        VerificationExample: VerificationExample
      response = {}
      response[d1.API_FIELDNAME] = d1
      fields = ['id', 'example', 'result', 'example'].join(',')
      url = d1.BASE_API_URL + "#{d1.id}/?show=" + fields
      $httpBackend.expectGET url
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.getPredictVectValue('nnn->1')).toEqual 'v1'
      expect($scope.getPredictVectValue('nnn->3')).toBe undefined


    it 'should return Raw Data Value', inject (VerificationExample)->
      $routeParams = {id: 888, verification_id: 777}
      d1 = new VerificationExample({id: 888, verification_id: 777, result: {raw_data: [{'nnn.1': 'v1'}]}})
      createController 'VerificationExampleDetailsCtrl',
        $routeParams: $routeParams
        VerificationExample: VerificationExample
      response = {}
      response[d1.API_FIELDNAME] = d1
      fields = ['id', 'example', 'result', 'example'].join(',')
      url = d1.BASE_API_URL + "#{d1.id}/?show=" + fields
      $httpBackend.expectGET url
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.getRawDataValue('nnn->1')).toEqual 'v1'
      expect($scope.getRawDataValue('nnn->3')).toBe undefined
