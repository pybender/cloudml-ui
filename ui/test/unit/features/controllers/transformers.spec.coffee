describe 'features/controllers/transformers.coffee', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.features.controllers.named_types'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.features.controllers.transformers'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  createController = null
  $scope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')

    createController = (ctrl, extras) ->
      $scope = $rootScope.$new()
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'TransformersTypesLoader', ->

    prepareContext = (feature) ->
      $rootScope.feature = feature
      createController 'TransformersTypesLoader'
      $scope.$digest()

    it 'should init scope and watch for transformer changes', inject (Transformer)->
      # new feature
      prepareContext {transformer: {}}

      expect(Transformer.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Transformer.$TYPES_LIST
      expect($scope.predefined_selected).toBe false

      $scope.feature.transformer = {id: 1}
      $scope.$digest()
      expect($scope.predefined_selected).toBe true

      $scope.feature.transformer = {id: -1}
      $scope.$digest()
      expect($scope.predefined_selected).toBe false

    it 'should handle transformer changes', ->
      prepareContext {transformer: {id: 10, type: 'zaza'}}
      expect($scope.predefined_selected).toBe true

      $scope.changeTransformer -1, 'zozo'

      expect($scope.feature.transformer.id).toBe -1
      expect($scope.feature.transformer.type).toEqual 'zozo'


  describe 'TransformersSelectLoader', ->

    it 'should load all pretrained transformers and handle errors', inject (Transformer)->

      transformer = new Transformer {id: 111, name: 'zozo'}

      response = {}
      response[transformer.API_FIELDNAME + 's'] = [transformer]
      $httpBackend.expectGET "#{transformer.BASE_API_URL}?show=name&status=Trained"
      .respond 200, angular.toJson response
      createController 'TransformersSelectLoader'
      $httpBackend.flush()

      expect($scope.pretrainedTransformers).toEqual = [transformer]

      # error handling
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'
      $httpBackend.expectGET "#{transformer.BASE_API_URL}?show=name&status=Trained"
      .respond 400
      createController 'TransformersSelectLoader'
      $httpBackend.flush()

      expect($rootScope.setError).toHaveBeenCalledWith jasmine.any(Object),
        'loading pretrained transformers'
      expect($scope.err).toEqual 'an error'


  describe 'TransformersListCtrl', ->

    it 'should init scope for transformer listing and implement add function',
      inject (Transformer)->
        createController 'TransformersListCtrl'

        expect($scope.MODEL).toEqual Transformer
        expect($scope.FIELDS).toEqual Transformer.MAIN_FIELDS
        expect($scope.ACTION).toEqual 'loading transformers'
        expect($scope.LIST_MODEL_NAME).toEqual Transformer.LIST_MODEL_NAME
        expect($scope.add).toBeDefined()

        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'

        # add dialog

        $scope.add()
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any(Transformer)
          template: 'partials/features/transformers/add.html'
          ctrlName: 'ModelWithParamsEditDialogCtrl'
          action: 'add transformer'
          path: 'transformers'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'TransformerDetailsCtrl', ->

    it 'should handle absence of route params', ->
      expect(->
        createController 'TransformerDetailsCtrl'
      ).toThrow new Error "Can't initialize transformer details controller without id"

    it 'should handle loading different sections with caching', inject (Transformer)->

      $rootScope.initSections = jasmine.createSpy '$scope.initSections'

      transformer = new Transformer {id: 222}
      response = {}
      response[transformer.API_FIELDNAME] = transformer
      $httpBackend.expectGET "#{transformer.BASE_API_URL}#{transformer.id}/?show=updated_on,created_on,status,name,created_by,updated_by,train_import_handler_type,train_import_handler,type,params,field_name,feature_type,json"
      .respond 200, angular.toJson response
      createController 'TransformerDetailsCtrl', {$routeParams: {id: 222}}
      $scope.goSection ['about', 'details']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['main', 'about']

      # a second go to same section should trigger http request
      $scope.goSection ['about', 'details']
      expect($scope.LOADED_SECTIONS).toEqual ['main', 'about']

      $httpBackend.expectGET "#{transformer.BASE_API_URL}#{transformer.id}/?show=,error,memory_usage,trainer_size,training_time,trained_by"
      .respond 200, angular.toJson response
      $scope.goSection ['training', '']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['main', 'about', 'training']

      # a second go to same section should trigger http request
      $scope.goSection ['about', 'details', 'training']
      expect($scope.LOADED_SECTIONS).toEqual ['main', 'about', 'training']

    it 'should handle load error', inject (Transformer)->

      $rootScope.initSections = jasmine.createSpy '$scope.initSections'
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'

      transformer = new Transformer {id: 222}
      response = {}
      response[transformer.API_FIELDNAME] = transformer
      $httpBackend.expectGET "#{transformer.BASE_API_URL}#{transformer.id}/?show=updated_on,created_on,status,name,created_by,updated_by,train_import_handler_type,train_import_handler,type,params,field_name,feature_type,json"
      .respond 400
      createController 'TransformerDetailsCtrl', {$routeParams: {id: 222}}
      $scope.goSection ['about', 'details']
      $httpBackend.flush()

      expect($rootScope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading transformer details'


  describe 'TransformerActionsCtrl', ->

    it 'should init scope', inject (Transformer)->

      createController 'TransformerActionsCtrl'
      expect(->
        $scope.init()
      ).toThrow new Error 'Please specify transformer'

      transformer = new Transformer {id: 444}
      $scope.init {transformer: transformer}

      expect($scope.transformer).toEqual transformer

    it 'should handle train action with errors', inject (Transformer)->

      $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
      createController 'TransformerActionsCtrl'
      transformer = new Transformer {id: 444}

      response = {}
      response[transformer.API_FIELDNAME] = transformer
      $httpBackend.expectGET "#{transformer.BASE_API_URL}#{transformer.id}/?show=train_import_handler,train_import_handler_type"
      .respond 200, angular.toJson response
      $scope.train(transformer)
      $httpBackend.flush()

      expect($rootScope.openDialog.calls.mostRecent().args[1]).toEqual
        model: transformer
        template: 'partials/models/model_train_popup.html'
        ctrlName: 'TrainModelCtrl'

      expect($rootScope.openDialog.calls.mostRecent().args[0]).toEqual $scope

      # with error
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'
      $httpBackend.expectGET "#{transformer.BASE_API_URL}#{transformer.id}/?show=train_import_handler,train_import_handler_type"
      .respond 400
      $scope.train(transformer)
      $httpBackend.flush()

      expect($rootScope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading import handler details'

    it 'should handle change type and delete action', inject (Transformer)->

      $rootScope.openDialog = (->)
      spyOn($rootScope, 'openDialog').and.returnValue {result: 'then': (->)}

      createController 'TransformerActionsCtrl'

      transformer = new Transformer {id: 555}

      $scope.changeType transformer
      expect($rootScope.openDialog.calls.mostRecent().args[1]).toEqual
        model: transformer
        template: 'partials/features/transformers/edit_type.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'

      expect($rootScope.openDialog.calls.mostRecent().args[0]).toEqual $scope

      $scope.delete transformer
      expect($rootScope.openDialog.calls.mostRecent().args[1]).toEqual
        model: transformer
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete transformer'
        path: transformer.BASE_UI_URL

      expect($rootScope.openDialog.calls.mostRecent().args[0]).toEqual $scope


