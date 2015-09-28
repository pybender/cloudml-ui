'use strict'

# jasmine specs for services go here

describe "service", ->

  beforeEach(module "ngCookies")
  beforeEach(module "app.services")

  $httpBackend = null
  $rootScope = null
  settings = null
  $cookieStore = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $cookieStore = $injector.get('$cookieStore')
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "version", ->
    it "should return current version", inject((version) ->
      expect(version).toEqual "0.1"
    )

  describe "auth", ->
    it "should request oauth url", inject((auth) ->
      url = settings.apiUrl + 'auth/get_auth_url'
      $httpBackend.expectPOST(url).respond('{"auth_url": "http://odesk.com/_fake"}')

      auth.login()
      $httpBackend.flush()
    )

    it "should send authorize request", inject((auth) ->
      url = settings.apiUrl + 'auth/authenticate?oauth_token=sometoken&oauth_verifier=someverifier'
      $httpBackend.expectPOST(url).respond('{"auth_token": "auth_token"}')

      auth.authorize('sometoken', 'someverifier')
      $httpBackend.flush()
    )

    it "should sign out the current user", inject((auth) ->
      $rootScope.user = {
        'uid': 'someuid'
      }

      auth.logout()
      expect($rootScope.user).toBeUndefined()
    )

    it "should request user info", inject((auth) ->
      $cookieStore.put('auth-token', 'auth_token')

      url = settings.apiUrl + 'auth/get_user'
      $httpBackend.expectPOST(url).respond('{"user": {"name": "Fiodor", "uid": "somebody"}}')

      auth.get_user()
      $httpBackend.flush()

      expect($rootScope.user.uid).toBe('somebody')
      expect($rootScope.user.name).toBe('Fiodor')
    )
