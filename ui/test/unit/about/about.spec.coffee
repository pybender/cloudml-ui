'use strict'

# jasmine specs for about

describe "about", ->

  beforeEach ->
    module 'ngCookies'

    module 'app'
    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.about.model'
    module 'app.about.controllers'

  $httpBackend = null
  $scope = null
  settings = null
  createController = null
  $rootScope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "AboutCtrl", ->

    it "should request about info and fill scope", inject () ->
      url = settings.apiUrl + 'about/'
      $httpBackend.expectGET(url).respond('{"about": {"version": "0.0.1"}}')
      createController "AboutCtrl"
      $httpBackend.flush()
      expect($scope.about.version).toEqual '0.0.1'

    it "should request about info and set error", inject () ->
      $scope.setError = jasmine.createSpy '$scope.setError'
      url = settings.apiUrl + 'about/'
      $httpBackend.expectGET(url).respond 500
      createController "AboutCtrl"
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading about info'

