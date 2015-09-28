'use strict'

# jasmine specs for weights

describe "Model Weights Controllers", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.models.model")
  beforeEach(module "app.importhandlers.models")
  beforeEach(module "app.importhandlers.xml.models")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.datas.model")

  beforeEach(module "app.weights.model")
  beforeEach(module "app.weights.controllers")

  $rootScope = null
  createController = null
  settings = null
  $controller = null
  $httpBackend = null
  $routeParams = null
  $scope = null

  beforeEach(inject(($injector) ->
    $rootScope = $injector.get('$rootScope')
    settings = $injector.get('settings')
    $controller = $injector.get('$controller')
    $httpBackend = $injector.get('$httpBackend')
    $routeParams = $injector.get('$routeParams')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "WeightsCtrl", ->

    beforeEach ->
      $routeParams.id = 'somemodelid'
      createController "WeightsCtrl"

      expect($scope.search_form).toBeDefined()

    it "should sort weights", inject () ->
      $scope.loadList = jasmine.createSpy()

      $scope.sort('somefield')
      expect($scope.loadList).toHaveBeenCalled()
      expect($scope.sort_by).toEqual('somefield')

    it "should load weights list", inject () ->
      url = settings.apiUrl + 'weights/somemodelid/?is_positive=0&order=asc&page=1&q=&show=' +
      'name,value,css_class,segment,value2' + '&sort_by=name'
      $httpBackend.expectGET(url).respond('{"weights": []}')

      # TODO: there're two same requests when action is weights:list
      $scope.action = ['weights', '']

      $scope.loadList()
      $httpBackend.flush()

    it "should load weights tree", inject () ->
      url = settings.apiUrl + 'weights_tree/somemodelid/?show=' +
      'name,short_name,parent,value2'
      $httpBackend.expectGET(url).respond('{"weights": [], "categories": []}')

      $scope.action = ['weights', '']

      $scope.loadTreeNode(undefined, true)
      $httpBackend.flush()

    it "should load weights brief list", inject () ->
      url = settings.apiUrl + 'weights/somemodelid/action/brief/?npage=1&ppage=1&segment=true&show=' +
      'name,value,css_class,segment_id'
      $httpBackend.expectGET(url).respond('{"negative_weights": [], "positive_weights": []}')

      $scope.action = ['weights', '']

      $scope.loadColumns(true, true)
      $httpBackend.flush()

    it "should load more positive weights", inject () ->
      url = settings.apiUrl + 'weights/somemodelid/action/brief/?npage=1&ppage=2&show=' +
      'name,value,css_class,segment_id'
      $httpBackend.expectGET(url).respond('{"negative_weights": [], "positive_weights": []}')

      $scope.action = ['weights', '']

      $scope.morePositiveWeights()
      $httpBackend.flush()

    it "should load more negative weights", inject () ->
      url = settings.apiUrl + 'weights/somemodelid/action/brief/?npage=2&ppage=1&show=' +
      'name,value,css_class,segment_id'
      $httpBackend.expectGET(url).respond('{"negative_weights": [], "positive_weights": []}')

      $scope.action = ['weights', '']

      $scope.moreNegativeWeights()
      $httpBackend.flush()
