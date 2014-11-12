describe 'features/controllers/transformers.coffee', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.features.controllers.named_types'
    module 'app.xml_importhandlers.models'
    module 'app.importhandlers.model'
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

    it 'should init scope ', inject (Scaler)->

      # new feature
      $rootScope.feature = {scaler: {}}
      createController 'ScalersTypesLoader'
      expect(Scaler.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Scaler.$TYPES_LIST
      expect($scope.predefined_selected).toBe false

      # featured editing with builtin feature
      $rootScope.feature = {id: 10, scaler: {type: Scaler.$TYPES_LIST[0]}}
      createController 'ScalersTypesLoader'
      expect(Scaler.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Scaler.$TYPES_LIST
      expect($scope.predefined_selected).toBe false

      # featured editing with predefined scaler
      $rootScope.feature = {id: 10, scaler: {type: 'zozo'}}
      createController 'ScalersTypesLoader'
      expect(Scaler.$TYPES_LIST.length).toBeGreaterThan 2
      expect($scope.types).toEqual Scaler.$TYPES_LIST
      expect($scope.predefined_selected).toBe true



