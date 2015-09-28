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
    module 'app.features.controllers.scalers'

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


  describe 'ScalersTypesLoader', ->

    prepareContext = (feature) ->
      $rootScope.feature = feature
      createController 'ScalersTypesLoader'
      $scope.$digest()

    it 'should init scope and watch for scaler changes', inject (Scaler)->
      # new feature
      prepareContext {scaler: {}}

      expect(Scaler.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Scaler.$TYPES_LIST
      expect($scope.predefined_selected).toBe false
      expect($scope.feature.scaler.predefined).toBeUndefined()

      $scope.feature.scaler.name = 'Bobo'
      $scope.$digest()
      expect($scope.predefined_selected).toBe true
      expect($scope.feature.scaler.predefined).toBe true

      $scope.feature.scaler.type = 'MinMaxScaler'
      $scope.$digest()
      expect($scope.predefined_selected).toBe false
      expect($scope.feature.scaler.predefined).toBe false

    it 'should respond to changing scaler builtin/predefined', inject (Scaler)->
      # new feature
      prepareContext {scaler: {type: 'MinMaxScaler'}}

      expect(Scaler.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Scaler.$TYPES_LIST
      expect($scope.predefined_selected).toBe false
      expect($scope.feature.scaler.predefined).toBe false

      $scope.changeScaler(true, 'zozo')
      expect($scope.predefined_selected).toBe true
      expect($scope.feature.scaler.predefined).toBe true
      expect($scope.feature.scaler.name).toEqual 'zozo'
      expect($scope.feature.scaler.type).toBe null

      $scope.changeScaler(false, 'zaza')
      expect($scope.predefined_selected).toBe false
      expect($scope.feature.scaler.predefined).toBe false
      expect($scope.feature.scaler.type).toEqual 'zaza'
      expect($scope.feature.scaler.name).toBe null

      $scope.changeScaler(true, null)
      expect($scope.predefined_selected).toBe true
      expect($scope.feature.scaler.predefined).toBe true
      expect($scope.feature.scaler.type).toBe null
      expect($scope.feature.scaler.name).toBe null

      $scope.changeScaler(false, null)
      expect($scope.predefined_selected).toBe false
      expect($scope.feature.scaler.predefined).toBe false
      expect($scope.feature.scaler.type).toBe null
      expect($scope.feature.scaler.name).toBe null

  describe 'ScalersSelectLoader', ->

    it 'should load all predefined scalers and handle errors', inject (Scaler)->

      scaler = new Scaler {name: 'zozo'}

      response = {}
      response[scaler.API_FIELDNAME + 's'] = [scaler]
      $httpBackend.expectGET "#{scaler.BASE_API_URL}?show=name"
      .respond 200, angular.toJson response
      createController 'ScalersSelectLoader'
      $httpBackend.flush()

      expect($scope.predefinedScalers).toEqual = [scaler]

      # error handling
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'
      $httpBackend.expectGET "#{scaler.BASE_API_URL}?show=name"
      .respond 400
      createController 'ScalersSelectLoader'
      $httpBackend.flush()

      expect($rootScope.setError).toHaveBeenCalledWith jasmine.any(Object),
        'loading predefined scalers'
      expect($scope.err).toEqual 'an error'
