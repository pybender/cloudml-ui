'use strict'

# jasmine specs for login

describe "login", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.login.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $modal = null
  $scope = null
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

    createController = (ctrl, extras) ->
      $scope = $rootScope.$new()
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "LoginCtl", ->

    it "should make no query", inject () ->
      createController "LoginCtl"
      expect($scope.is_authenticated).toBeFalsy()

    it "should do redirect", inject () ->
      createController "LoginCtl"
      $scope.authenticate()

      expect($location.path).toHaveBeenCalledWith('/auth/authenticate')

  describe "AuthCtl", ->

    it "should redirect to oDesk authorization", inject (auth)->
      url = settings.apiUrl + 'auth/get_auth_url'
      $httpBackend.expectPOST(url).respond('{"auth_url": "http://odesk.com/_fake"}')

      $window =
        location:
          replace: jasmine.createSpy 'window.location.replace'
      spyOn(auth, 'is_authenticated').andReturn false

      createController "AuthCtl", {$window: $window, auth: auth}
      expect($scope.status).toBe('Getting data. Please wait...')

      $httpBackend.flush()
      expect($scope.status).toBe('Redirecting to oDesk. Please wait...')
      expect($window.location.replace).toHaveBeenCalledWith('http://odesk.com/_fake')
      expect(auth.is_authenticated.callCount).toBe 1

    it "should make no query if already logged in", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCtl"

      expect($scope.status).toBe('Already logged in')
      expect($scope.is_authenticated).toBeTruthy()

  describe "AuthCallbackCtl", ->

    it "should authorize and reload the page", inject (auth) ->
      spyOn($location, 'search').andReturn({
        oauth_token: 'oauth_token',
        oauth_verifier: 'oauth_verifier'
      })
      $window =
        location:
          reload: jasmine.createSpy '$window.location.reload'

      url = settings.apiUrl + 'auth/authenticate?oauth_token=oauth_token&oauth_verifier=oauth_verifier'
      $httpBackend.expectPOST(url).respond('{"auth_token": "auth_token"}')

      createController "AuthCallbackCtl", {$window: $window}
      expect($scope.status).toBe('Authorization. Please wait...')
      expect($scope.is_authenticated).toBeFalsy()

      $httpBackend.flush()
      expect($scope.status).toBe('Authorized')
      expect($window.location.reload).toHaveBeenCalled()
      expect(auth.is_authenticated()).toBeTruthy()

    it "should make no query if already logged in", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCallbackCtl"

      expect($scope.status).toBe('Already logged in')
      expect($scope.is_authenticated).toBeTruthy()

  describe "UserCtl", ->

    it "should make no query", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "UserCtl"

    it "should request user info", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "UserCtl"

      url = settings.apiUrl + 'auth/get_user'
      $httpBackend.expectPOST(url).respond('{"user": {"name": "Fiodor", "uid": "somebody"}}')

      $scope.init()
      $httpBackend.flush()

      expect($scope.user.uid).toBe('somebody')
      expect($scope.user.name).toBe('Fiodor')
