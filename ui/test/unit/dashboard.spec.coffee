'use strict'

# jasmine specs for dashboard

describe "dashboard", ->

  beforeEach(module "ngCookies")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.base")

  beforeEach(module "app.dashboard.controllers")
  beforeEach(module "app.dashboard.model")

  beforeEach(module "app.models.model")
  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.xml_importhandlers.models")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.features.models")
  beforeEach(module "app.testresults.model")

  $httpBackend = null
  $rootScope = null
  settings = null
  createController = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')

    createController = (ctrl) ->
       $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "DashboardCtrl", ->

    it "should request statictics and define styles map", inject () ->
      url = settings.apiUrl + 'statistics/'
      $httpBackend.expectGET(url).respond('{"statistics": []}')

      # TODO: why "undefined"?
      # url = settings.apiUrl + 'models/undefined/tests/action/examples_size/'
      # $httpBackend.expectGET(url).respond('{"tests": []}')

      createController "DashboardCtrl"
      $httpBackend.flush()

      expect($rootScope.STYLES_MAP).toBeDefined()
