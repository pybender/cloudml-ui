'use strict'

# jasmine specs for login

describe "login", ->

  beforeEach ->
    module "ngCookies"
    module "ngRoute"
    module "ui.bootstrap"

    module "app.base"
    module "app.config"
    module "app.services"
    module 'app'

    module "app.login.controllers"

    # the following just to inject Model
    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.datasets.model'
    module 'app.features.models'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $scope = null
  createController = null

  beforeEach(inject(($injector) ->
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

      expect($location.path()).toEqual '/auth/authenticate'

  describe "AuthCtl", ->

    it "should redirect to Upwork authorization", inject (auth)->
      url = settings.apiUrl + 'auth/get_auth_url'
      $httpBackend.expectPOST(url).respond('{"auth_url": "http://odesk.com/_fake"}')

      $window =
        location:
          replace: jasmine.createSpy 'window.location.replace'
      spyOn(auth, 'is_authenticated').and.returnValue false

      createController "AuthCtl", {$window: $window, auth: auth}
      expect($scope.status).toBe('Getting data. Please wait...')

      $httpBackend.flush()
      expect($scope.status).toBe('Redirecting to Upwork. Please wait...')
      expect($window.location.replace).toHaveBeenCalledWith('http://odesk.com/_fake')
      expect(auth.is_authenticated.calls.count()).toBe 1

    it "should make no query if already logged in", inject ($cookieStore) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCtl"

      expect($scope.status).toBe('Already logged in')
      expect($scope.is_authenticated).toBeTruthy()

  describe "AuthCallbackCtl", ->

    it "should authorize and reload the page", inject (auth) ->
      spyOn($location, 'search').and.returnValue({
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

    it "should make no query if already logged in", inject ($cookieStore, Model) ->
      $cookieStore.put('auth-token', 'auth_token')
      createController "AuthCallbackCtl"

      expect($scope.status).toBe('Already logged in')
      model = new Model
      expect($location.url()).toEqual model.BASE_UI_URL

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
