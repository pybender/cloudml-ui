'use strict'

describe "app", ->

  beforeEach ->
    module 'ngCookies'
    module 'ui.bootstrap'

    module 'app'
    module 'app.services'

  $rootScope = null
  settings = null
  $httpBackend = null
  $scope = null
  $modal = null
  $routeParams = null
  $location = null
  $auth = null
  $cookieStore = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $modal = $injector.get('$modal')
    $scope = $rootScope.$new()
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $auth = $injector.get('auth')
    $cookieStore = $injector.get '$cookieStore'
    spyOn $modal, 'open'
    spyOn $auth, 'logout'
    spyOn $auth, 'is_authenticated'
    spyOn $cookieStore, 'put'
    spyOn $cookieStore, 'get'
    spyOn($location, 'url').and.callThrough()
    spyOn($location, 'path').and.callThrough()

  afterEach ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()

  describe '$rootScope', ->

    it 'should initialize $rootScope', ->

      expect($scope.loadingCount).toBe 0
      expect($scope.errorList).toEqual {}

    it 'should setFieldError & resetError', ->
      expect($scope.setFieldError).toEqual jasmine.any(Function)
      expect($scope.resetError).toEqual jasmine.any(Function)

      $scope.setFieldError 'err1', 'msg1'
      expect($scope.errorList).toEqual {err1: 'msg1'}
      $scope.setFieldError 'err2'
      expect($scope.errorList).toEqual {err1: 'msg1', err2: ''}
      $scope.resetError()
      expect($scope.errorList).toEqual {}

    describe 'openDialog', ->

      it 'should raise error when no scope or no template', ->
        expect ->
          $scope.openDialog()
        .toThrow new Error('scope is required')

        expect ->
          $scope.openDialog {}, {}
        .toThrow new Error('template is required')

      it 'should call $modal.open', ->
        expect($scope.openDialog).toEqual jasmine.any(Function)

        opts =
          template: '/some/template/or/url'
          ctrlName: 'SomeControllerName'
          cssClass: 'windowCSSClass'
        $scope.openDialog $scope, opts

        expect($modal.open).toHaveBeenCalledWith
          scope: $scope
          templateUrl: opts.template
          controller: opts.ctrlName
          windowClass: opts.cssClass
          resolve:
            openOptions: jasmine.any Function

    describe 'initSections', ->
      beforeEach ->
        expect($scope.initSections).toEqual jasmine.any(Function)

      it 'should call initSections default model:details', ->

        goFn = jasmine.createSpy 'goFn'
        $scope.initSections goFn

        expect($scope.action).toEqual ['model', 'details']
        expect($scope.goSection).toEqual goFn
        expect($scope.isSimpleTabs).toBe false
        expect($scope.initializedSections).toEqual []
        expect(goFn).toHaveBeenCalledWith ['model', 'details']

      it 'should call initSections with non default action', ->

        goFn = jasmine.createSpy 'goFn'
        $scope.initSections goFn, 'some:section', true

        expect($scope.action).toEqual ['some', 'section']
        expect($scope.goSection).toEqual goFn
        expect($scope.isSimpleTabs).toBe true
        expect($scope.initializedSections).toEqual []
        expect(goFn).toHaveBeenCalledWith ['some', 'section']

      it 'should call initSections with $routeParams.action', ->

        goFn = jasmine.createSpy 'goFn'
        $routeParams.action = 'route:params:action'
        $scope.initSections goFn

        expect($scope.action).toEqual ['route', 'params', 'action']
        expect($scope.goSection).toEqual goFn
        expect($scope.isSimpleTabs).toBe false
        expect($scope.initializedSections).toEqual []
        expect(goFn).toHaveBeenCalledWith ['route', 'params', 'action']

    describe 'setSection', ->
      beforeEach ->
        expect($scope.initSections).toEqual jasmine.any(Function)
        expect($scope.setSection).toEqual jasmine.any(Function)

      doSpecification = (simpleTabs) ->
        goFn = jasmine.createSpy 'goFn'
        $scope.initSections goFn, 'model:details', simpleTabs

        goFn.calls.reset()
        $scope.setSection ['model', 'details'] # this value coming from DEFAULT_ACTION in app.coffee

        expect($scope.action).toEqual ['model', 'details']
        expect($location.search()).toEqual {}
        expect($scope.initializedSections).toEqual ['model:details']
        expect($scope.goSection.calls.count()).toEqual 1

        # going to another section
        goFn.calls.reset()
        $scope.setSection ['new', 'section']
        expect($scope.action).toEqual ['new', 'section']
        expect($location.search()).toEqual { action : 'new:section' }
        expect($scope.initializedSections).toEqual ['model:details', 'new:section']
        expect($scope.goSection.calls.count()).toEqual 1

        # back to model:datails, going will depend on simpleTabs=true
        goFn.calls.reset()
        $scope.setSection ['model', 'details']
        expect($scope.action).toEqual ['model', 'details']
        expect($location.search()).toEqual { }
        expect($scope.initializedSections).toEqual ['model:details', 'new:section']
        expect($scope.goSection.calls.count()).toEqual if simpleTabs then 0 else 1

        # back too model:datails
        goFn.calls.reset()
        $scope.setSection ['new', 'section']
        expect($scope.action).toEqual ['new', 'section']
        expect($location.search()).toEqual { action : 'new:section' }
        expect($scope.initializedSections).toEqual ['model:details', 'new:section']
        expect($scope.goSection.calls.count()).toEqual if simpleTabs then 0 else 1

      it 'simpletabs case, should go to section or not based on initialized sections and update $location.search accordingly', ->

        doSpecification true

      it 'not simpletabs case, should go to section or not based on initialized sections and update $location.search accordingly', ->

        doSpecification false

    describe 'resetError', ->
      beforeEach ->
        expect($scope.resetError).toEqual jasmine.any(Function)
        $rootScope.err = 'some error'
        $rootScope.statusCode = 'some status'
        $rootScope.errorList = {err1: 'error1'}
        expect($scope.err).toEqual $rootScope.err
        expect($scope.statusCode).toEqual $rootScope.statusCode
        expect($scope.errorList).toEqual $rootScope.errorList

      it 'should reset error', ->

        $scope.resetError()
        expect($scope.err).toEqual ''
        expect($scope.statusCode).toEqual null
        expect($scope.errorList).toEqual {}

      it 'should respond to $routeChangeStart with reseting error', ->

        $scope.$emit '$routeChangeStart', {}
        expect($scope.err).toEqual ''
        expect($scope.statusCode).toEqual null
        expect($scope.errorList).toEqual {}

    describe 'setError', ->

      beforeEach ->
        $rootScope.setFieldError = jasmine.createSpy '$rootScope.setFieldError'

      it 'should set the error with no options', ->

        retErr = $scope.setError {}, 'the_message'
        expect(retErr).toContain ' the_message'
        expect($scope.err).toEqual retErr
        expect($scope.statusCode).toBeUndefined()

      it 'should set the error with options', ->

        retErr = $scope.setError
          data:
            response:
              error:
                errors: ['err1', 'err2', 'err3']
          status: 'the_status'

        , 'the_message'
        expect(retErr).toContain ' the_message'
        expect(retErr).toContain ' the_status'
        expect($scope.setFieldError.calls.count()).toEqual 3
        expect($scope.err).toEqual retErr
        expect($scope.statusCode).toEqual 'the_status'

      it 'should logout', ->
        $scope.setError {status: 401}
        expect($auth.logout).toHaveBeenCalled()
        expect($location.path()).toEqual '/auth/login'

    describe '$routeChangeStart authentication log', ->

      it 'not authenticated going to protected resource', ->
        $auth.is_authenticated.and.returnValue false

        $location.url '/some/location/protected'
        $scope.$emit '$routeChangeStart', {$route: {controller: 'zinger'}}
        expect($cookieStore.put).toHaveBeenCalledWith 'redirect_to', '/some/location/protected'
        expect($location.path()).toEqual '/auth/login'

      it 'authenticated going to protected resource but not from authentication controllers', ->
        $auth.is_authenticated.and.returnValue true

        $location.url '/some/location/protected'
        $scope.$emit '$routeChangeStart', {$route: {controller: 'zinger'}}
        expect($cookieStore.put).not.toHaveBeenCalled()
        expect($cookieStore.get).not.toHaveBeenCalled()


      describe 'not authenticated going to login resource, one with controller LoginCtl, AuthCtl, AuthCallbackCtl', ->
        beforeEach ->
          $auth.is_authenticated.and.returnValue false

        doSpec = (ctrl)->
          $location.url '/auth/login/for/login'
          $scope.$emit '$routeChangeStart', {$route: {controller: ctrl}}
          expect($cookieStore.put).not.toHaveBeenCalled()
          expect($location.path()).toEqual '/auth/login/for/login'

        it 'not authenticated going to login resource, LoginCtl', ->
          doSpec 'LoginCtl'

        it 'not authenticated going to login resource, AuthCtl', ->
          doSpec 'AuthCtl'

        it 'not authenticated going to login resource, AuthCallbackCtl', ->
          doSpec 'AuthCallbackCtl'


      describe 'authenticated going to login resource, one with controller LoginCtl, AuthCtl, AuthCallbackCtl', ->
        beforeEach ->
          $auth.is_authenticated.and.returnValue true


        doSpec = (ctrl, cookieUrl=null)->
          if cookieUrl
            $cookieStore.get.and.returnValue cookieUrl
          $location.url '/auth/login/for/login'
          $scope.$emit '$routeChangeStart', {$route: {controller: ctrl}}
          expect($cookieStore.get).toHaveBeenCalled()
          if cookieUrl
            expect($location.url).toHaveBeenCalledWith cookieUrl
          else
            expect($location.path).toHaveBeenCalledWith '/models'

        it 'authenticated going to login resource, LoginCtl and no redirect', ->
          doSpec 'LoginCtl'

        it 'authenticated going to login resource, LoginCtl and redirect', ->
          doSpec 'LoginCtl', '/redirect/to/this/url'

        it 'authenticated going to login resource, AuthCtl', ->
          doSpec 'AuthCtl'

        it 'authenticated going to login resource, AuthCtrl and redirect', ->
          doSpec 'AuthCtl', '/redirect/to/this/url'

        it 'authenticated going to login resource, AuthCallbackCtl', ->
          doSpec 'AuthCallbackCtl'

        it 'authenticated going to login resource, AuthCallbackCtl and redirect', ->
          doSpec 'AuthCallbackCtl', '/redirect/to/this/url'
