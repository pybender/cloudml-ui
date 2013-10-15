'use strict'

# jasmine specs for logmessages

describe "logmessages", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.logmessages.controllers")
  beforeEach(module "app.logmessages.model")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $dialog = null
  createController = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $dialog = $injector.get('$dialog')

    spyOn($location, 'path')

    createController = (ctrl) ->
      $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "LogMessageListCtrl", ->

    it "should make no query", inject () ->
      createController "LogMessageListCtrl"

    it "should set options", inject () ->
      createController "LogMessageListCtrl"
      $rootScope.init()
      expect($rootScope.log_levels).toBeDefined()
      expect($rootScope.log_level).toBeDefined()

    it "should call 'load' method", inject () ->
      createController "LogMessageListCtrl"

      $rootScope.load = jasmine.createSpy()

      $rootScope.init('type', 'some_obj_id')
      $rootScope.log_level = 'WARNING'
      $rootScope.setLogLevel()

      expect($rootScope.kwargs['level']).toBe('WARNING')
      expect($rootScope.load).toHaveBeenCalled()
