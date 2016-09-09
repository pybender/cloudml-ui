'use strict'

# jasmine specs for logmessages

describe "logmessages", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
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
  $modal = null
  createController = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $modal = $injector.get('$modal')

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
      $rootScope.load = jasmine.createSpy()
      $rootScope.init()
      expect($rootScope.log_levels).toBeDefined()
      expect($rootScope.log_level).toBeDefined()
      expect($rootScope.load).toHaveBeenCalled()

    it "should call 'load' method", inject () ->
      createController "LogMessageListCtrl"

      $rootScope.load = jasmine.createSpy()

      $rootScope.init('type', 'some_obj_id')
      $rootScope.log_level = 'WARNING'
      $rootScope.setLogLevel()

      expect($rootScope.params['level']).toBe('WARNING')
      expect($rootScope.load).toHaveBeenCalled()

    it 'should parse and set traceback', inject () ->
      createController "LogMessageListCtrl"
      $rootScope.showTraceback('[{"line": "myline"}]')
      expect($rootScope.trace).toEqual [{'line': 'myline'}]

      $rootScope.showTraceback("incorrect[]")
      expect($rootScope.trace).toEqual [[{"line": "Traceback can't be parsed"}]]

