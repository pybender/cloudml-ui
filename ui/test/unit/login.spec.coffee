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

  describe "LoginCtl", ->

    it "should make no query", inject () ->
      createController "LoginCtl"
      expect($rootScope.is_authenticated).toBeFalsy()

    it "should do redirect", inject () ->
      createController "LoginCtl"
      $rootScope.authenticate()

      expect($location.path).toHaveBeenCalledWith('/auth/authenticate')

  describe "AuthCtl", ->

    it "should redirect to oDesk authorization", inject () ->
      url = settings.apiUrl + 'auth/get_auth_url?'
      $httpBackend.expectPOST(url).respond('{"auth_url": "http://odesk.com/_fake"}')

      spyOn(window, '$cml_window_location_replace').andCallFake(() -> null)

      createController "AuthCtl"
      expect($rootScope.status).toBe('Getting data. Please wait...')

      $httpBackend.flush()
      expect($rootScope.status).toBe('Redirecting to oDesk. Please wait...')
      expect($cml_window_location_replace).toHaveBeenCalledWith('http://odesk.com/_fake')

    it "should make no query if already logged in", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCtl"

      expect($rootScope.status).toBe('Already logged in')
      expect($rootScope.is_authenticated).toBeTruthy()

  describe "AuthCallbackCtl", ->

    it "should authorize and reload the page", inject (auth) ->
      spyOn(window, '$cml_window_location_reload').andCallFake(() -> null)
      spyOn($location, 'search').andReturn({
        oauth_token: 'oauth_token',
        oauth_verifier: 'oauth_verifier'
      })

      url = settings.apiUrl + 'auth/authenticate?oauth_token=oauth_token&oauth_verifier=oauth_verifier'
      $httpBackend.expectPOST(url).respond('{"auth_token": "auth_token"}')

      createController "AuthCallbackCtl"
      expect($rootScope.status).toBe('Authorization. Please wait...')
      expect($rootScope.is_authenticated).toBeFalsy()

      $httpBackend.flush()
      expect($rootScope.status).toBe('Authorized')
      expect($cml_window_location_reload).toHaveBeenCalled()
      expect(auth.is_authenticated()).toBeTruthy()

    it "should make no query if already logged in", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCallbackCtl"

      expect($rootScope.status).toBe('Already logged in')
      expect($rootScope.is_authenticated).toBeTruthy()

  describe "UserCtl", ->

    it "should make no query", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "UserCtl"

    it "should request user info", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "UserCtl"

      url = settings.apiUrl + 'auth/get_user?'
      $httpBackend.expectPOST(url).respond('{"user": {"name": "Fiodor", "uid": "somebody"}}')

      $rootScope.init()
      $httpBackend.flush()

      expect($rootScope.user.uid).toBe('somebody')
      expect($rootScope.user.name).toBe('Fiodor')
