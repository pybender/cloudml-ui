describe 'controllers.coffee', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.controllers'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.datas.model'
    module 'app.testresults.model'
    module 'app.models.model'
    module 'app.datasets.model'
    module 'app.features.models'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null
  $q = null
  $rootScope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $scope = $rootScope.$new()
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')
    $q = $injector.get('$q')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'AppCtrl', ->

    it 'should init scope', ->

      createController 'AppCtrl', {$location: $location, $rootScope: $scope}

      expect($scope.$location).toEqual $location
      expect($scope.pathElements).toEqual []
      expect(_.keys($scope.codeMirrorConfigs()).length).toEqual 4

    it 'should watch location changes', ->

        createController 'AppCtrl', {$location: $location, $rootScope: $scope}

        expect($scope.$location).toEqual $location
        expect($scope.pathElements).toEqual []

        $location.path('models/123')
        $scope.$digest()
        $scope.$emit '$routeChangeSuccess'

        expect($scope.pathElements).toEqual [
          name : 'models'
          path : '/models'
        ,
          name : '123'
          path : '/models/123'
        ]
        expect($scope.activeNavId).toEqual '/models/123'
        expect($scope.getClass '/models').toEqual 'active'
        expect($scope.getClass '/handlers').toEqual ''


  describe 'ObjEditCtrl', ->

    it 'should call save and handle errors',
      inject (XmlImportHandler)->

        handler = new XmlImportHandler
          id: 1
          name: 'zozo'
        response = {}
        response[handler.API_FIELDNAME] = handler
        $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 200, angular.toJson(response)

        $scope.model = handler
        createController 'ObjEditCtrl'
        expect($scope.save).toBeDefined()
        $scope.save ['id', 'name']
        $httpBackend.flush()

        # error
        $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue 'An Err'
        $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 400
        $scope.save ['id', 'name']
        $httpBackend.flush()
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.err).toEqual 'An Err'

  describe 'SaveObjectCtl', ->

    it 'should init scope, save model and handler save errors',
      inject (XmlImportHandler)->

        handler = new XmlImportHandler
          id: 1
          name: 'zaza'
        response = {}
        response[handler.API_FIELDNAME] = handler
        $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 200, angular.toJson(response)

        $scope.$emit = jasmine.createSpy '$scope.$emit'
        createController 'SaveObjectCtl', {$location: $location, $timeout: $timeout}
        $scope.init handler
        expect($scope.model).toEqual handler

        $scope.LIST_MODEL_NAME = 'zinger'
        $scope.DONT_REDIRECT = false
        $scope.save ['id', 'name']
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.savingProgress).toEqual '100%'
        expect($scope.saving).toBe true
        expect($scope.$emit.calls.argsFor(0)[0]).toEqual 'SaveObjectCtl:save:success'
        expect($scope.$emit.calls.argsFor(0)[1]).toEqual handler
        expect($scope.$emit.calls.argsFor(1)[0]).toEqual 'BaseListCtrl:start:load'
        expect($scope.$emit.calls.argsFor(1)[1]).toEqual $scope.LIST_MODEL_NAME
        expect($location.path()).toEqual $location.path()

        # error
        $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue 'An Err'
        $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 400
        $scope.save ['id', 'name']
        $httpBackend.flush()
        $timeout.flush()
        expect($scope.savingProgress).toEqual '0%'
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.err).toEqual 'An Err'

  describe 'ObjectListCtrl', ->

    it 'should init scope & respond to page changes and filter changes',
      inject (Data, TestResult)->

        $scope.filter_opts = {}
        createController 'ObjectListCtrl', {$q: $q, $timeout: $timeout}

        expect($scope.page).toEqual 1
        expect($scope.total).toEqual 0
        expect($scope.per_page).toEqual 20
        expect($scope.objects).toEqual []
        expect($scope.loading).toBe false
        expect($scope.init).toThrow new Error 'Invalid object loader supplied to ObjectListCtrl'

        $scope.test = new TestResult
          id: 999
          model_id: 888

        data = new Data
          id: 7777
          test_id: $scope.test.id
          model_id: $scope.test.model_id

        show = 'id,name,label,pred_label,title,prob,example_id'
        order = 'desc'
        objectLoader = (opts) ->
          filter_opts = opts.filter_opts
          delete opts.filter_opts
          opts = _.extend({show: show}, opts, filter_opts)
          $scope.loading_state = true
          opts.sort_by = $scope.sort_by
          opts.order = if $scope.asc_order then 'asc' else 'desc'
          Data.$loadAll($scope.test.model_id, $scope.test.id, opts).then((resp) ->
            $scope.loading_state = false
            return resp
          )

        spyOn($scope, 'load').and.callThrough()
        spyOn($scope, '$broadcast').and.callThrough()

        url = "#{data.BASE_API_URL}?order=#{order}&page=#{$scope.page}&show=#{show}"
        response = angular.fromJson(map_url_to_response(url, 'loading examples of a test with paging')[1])
        $httpBackend.expectGET url
        .respond 200, angular.toJson response
        $scope.init {objectLoader: objectLoader}
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.objectLoader).toEqual objectLoader
        expect($scope.load).toHaveBeenCalled()

        expect($scope.loading).toBe false
        expect($scope.total).toBe 3480 # look at canned_responses response
        expect($scope.page).toBe 1
        expect($scope.pages).toBe 174  # look at canned_responses response
        expect($scope.per_page).toBe 20 # look at canned_responses response
        expect($scope.objects).toEqual jasmine.any(Array)
        expect($scope.$broadcast).toHaveBeenCalledWith 'ObjectListCtrl:load:success', $scope.objects

        # changing the page
        page = 2
        url = "#{data.BASE_API_URL}?order=#{order}&page=#{page}&show=#{show}"
        response = angular.fromJson(map_url_to_response(url, 'loading examples of a test with paging')[1])
        response.page = page
        $httpBackend.expectGET url
        .respond 200, angular.toJson response
        $scope.page = page
        $scope.$digest()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.loading).toBe false
        expect($scope.total).toBe 3480 # look at canned_responses response
        expect($scope.page).toBe 2
        expect($scope.pages).toBe 174  # look at canned_responses response
        expect($scope.per_page).toBe 20 # look at canned_responses response
        expect($scope.objects).toEqual jasmine.any(Array)
        expect($scope.$broadcast).toHaveBeenCalledWith 'ObjectListCtrl:load:success', $scope.objects

        # changing the page with error
        page = 3
        url = "#{data.BASE_API_URL}?order=#{order}&page=#{page}&show=#{show}"
        $httpBackend.expectGET url
        .respond 400
        $scope.page = page
        $scope.$digest()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.loading).toBe false
        expect($scope.total).toBe 3480 # look at canned_responses response
        expect($scope.page).toBe 2
        expect($scope.pages).toBe 174  # look at canned_responses response
        expect($scope.per_page).toBe 20 # look at canned_responses response
        expect($scope.objects).toEqual jasmine.any(Array)
        expect($scope.$broadcast).toHaveBeenCalled()
        expect($scope.$broadcast.calls.mostRecent().args[0]).toEqual 'ObjectListCtrl:load:error'

        # changing filter options
        page = 2 # the latest success retrieval
        url = "#{data.BASE_API_URL}?order=#{order}&page=#{page}&show=#{show}&zozo=zaza"
        response = angular.fromJson(map_url_to_response(url, 'loading examples of a test with paging')[1])
        $scope.filter_opts = {zozo: 'zaza'}
        response.page = page
        $httpBackend.expectGET url
        .respond 200, angular.toJson response
        $scope.page = page
        $scope.$digest()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.loading).toBe false
        expect($scope.total).toBe 3480 # look at canned_responses response
        expect($scope.page).toBe 2
        expect($scope.pages).toBe 174  # look at canned_responses response
        expect($scope.per_page).toBe 20 # look at canned_responses response
        expect($scope.objects).toEqual jasmine.any(Array)
        expect($scope.$broadcast).toHaveBeenCalledWith 'ObjectListCtrl:load:success', $scope.objects
        expect($scope.filter_opts).toEqual {zozo: 'zaza'}


        # changing filter options wit error
        page = 2 # the latest success retrieval
        url = "#{data.BASE_API_URL}?order=#{order}&page=#{page}&show=#{show}&zinger=zinger2"
        $httpBackend.expectGET url
        .respond 400
        $scope.filter_opts = {zinger: 'zinger2'}
        $scope.page = page
        $scope.$digest()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.loading).toBe false
        expect($scope.total).toBe 3480 # look at canned_responses response
        expect($scope.page).toBe 2
        expect($scope.pages).toBe 174  # look at canned_responses response
        expect($scope.per_page).toBe 20 # look at canned_responses response
        expect($scope.objects).toEqual jasmine.any(Array)
        expect($scope.$broadcast.calls.mostRecent().args[0]).toEqual 'ObjectListCtrl:load:error'
        expect($scope.filter_opts).toEqual {zozo: 'zaza'}

  describe 'BaseDeleteCtrl', ->

    it 'should init scope & calls delete',
      inject (XmlImportHandler, $location, $timeout)->

        handler = new XmlImportHandler
          id: 999
        $scope.resetError = jasmine.createSpy '$scope.resetError'
        $scope.$close = jasmine.createSpy '$scope.$close'
        $scope.$emit = jasmine.createSpy '$scope.$emit'
        $scope.model = handler
        $scope.LIST_MODEL_NAME = 'something'
        $scope.path = '/new/path'

        createController 'BaseDeleteCtrl'
        $scope.$emit = jasmine.createSpy '$scope.ownerScope.$emit'
        expect($scope.resetError).toHaveBeenCalled()

        # successful delete
        $httpBackend.expectDELETE "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 200
        $scope.delete()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.$close).toHaveBeenCalled()
        expect($scope.$emit).toHaveBeenCalledWith 'modelDeleted', [handler]
        expect($scope.$emit).toHaveBeenCalledWith 'BaseListCtrl:start:load', 'something'
        expect($location.url()).toEqual $scope.path

        # error delete
        $scope.setError = jasmine.createSpy '$scope.setError'
        $scope.$close.calls.reset()
        $scope.$emit.calls.reset()
        $scope.$emit.calls.reset()
        $httpBackend.expectDELETE "#{handler.BASE_API_URL}#{handler.id}/"
        .respond 400
        $scope.delete()
        $httpBackend.flush()
        $timeout.flush()

        expect($scope.$close).not.toHaveBeenCalled()
        expect($scope.$emit).not.toHaveBeenCalledWith 'modelDeleted', [handler]
        expect($scope.$emit).not.toHaveBeenCalledWith 'BaseListCtrl:start:load', 'something'
        expect($scope.setError).toHaveBeenCalled()


  describe 'DialogCtrl', ->

    it 'should init', ->
      openOptions =
        action: 'action'
        model:
          some: 'model'
        path: '/some/path'
        ownerSocpe:
          some: 'owner scope'

      $scope.resetError = jasmine.createSpy '$scope.resetError'
      createController 'DialogCtrl', {openOptions: openOptions}

      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.MESSAGE).toEqual openOptions.action
      expect($scope.model).toEqual openOptions.model
      expect($scope.path).toEqual openOptions.path
      expect($scope.action).toEqual openOptions.action
      expect($scope.ownerScope).toEqual openOptions.ownerScope


  describe 'BaseListCtrl', ->

    it 'should init scope & handle load error',
      inject (XmlImportHandler)->

        handler = new XmlImportHandler
          id: 111
          name: 'handler111'
        $scope.FIELDS = 'id,name'
        $scope.MODEL = XmlImportHandler

        spyOn($scope, '$emit').and.callThrough()
        createController 'BaseListCtrl', {$rootScope: $rootScope}

        expect($scope.init).toBeDefined()
        expect($scope.load).toBeDefined()
        expect($scope.loadMore).toBeDefined()

        # init & load error
        $scope.$emit.calls.reset()
        $scope.setError = jasmine.createSpy '$scope.setError'
        $httpBackend.expectGET "#{handler.BASE_API_URL}?show=id,name"
        .respond 400
        $scope.init()
        $httpBackend.flush()
        expect($scope.setError).toHaveBeenCalled()
        expect($scope.$emit).not.toHaveBeenCalled()

    describe 'load operations and event handling', ->

      handler = null

      beforeEach inject (XmlImportHandler)->
        handler = new XmlImportHandler
          id: 111
          name: 'handler111'
        $scope.FIELDS = 'id,name'
        $scope.MODEL = XmlImportHandler

        spyOn($scope, '$emit').and.callThrough()
        createController 'BaseListCtrl', {$rootScope: $rootScope}

        expect($scope.init).toBeDefined()
        expect($scope.load).toBeDefined()
        expect($scope.loadMore).toBeDefined()
        expect($scope.sort_list).toBeDefined()

        # init scope & load
        response =
          pages: 2
          has_next: true
        response[handler.API_FIELDNAME + 's'] = [handler]
        $httpBackend.expectGET "#{handler.BASE_API_URL}?show=id,name"
        .respond 200, angular.toJson(response)
        $scope.init()
        $httpBackend.flush()

      it 'should init scope & load', ->
        expect($scope.pages).toEqual 2
        expect($scope.has_next).toBe true
        expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [{id: 111, name: 'handler111'}]
        expect($scope.$emit).toHaveBeenCalledWith 'BaseListCtrl:load:success', $scope.objects

      it 'should respond to loadMore', inject (XmlImportHandler)->
          # loadMore concats objects
          handler2 = new XmlImportHandler
            id: 222
            name: 'handler222'
          $scope.kwargs =
            page: 1
          response =
            pages: 2
            has_next: true
          response[handler.API_FIELDNAME + 's'] = [handler2]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?page=2&show=id,name,page"
          .respond 200, angular.toJson(response)
          $scope.loadMore()
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [
            {id: 111, name: 'handler111'}
            {id: 222, name: 'handler222'}
          ]
          expect($scope.$emit).toHaveBeenCalledWith 'BaseListCtrl:load:success', $scope.objects

      it 'should respond to BaseListCtrl:start:load', inject (XmlImportHandler)->
          handler3 = new XmlImportHandler
            id: 333
            name: 'handler333'
          $scope.kwargs =
            page: 1
          response =
            pages: 2
            has_next: true
          $scope.modelName = XmlImportHandler.LIST_MODEL_NAME
          response[handler.API_FIELDNAME + 's'] = [handler3]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?page=1&show=id,name,page"
          .respond 200, angular.toJson(response)
          $scope.$emit 'BaseListCtrl:start:load', XmlImportHandler.LIST_MODEL_NAME
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [{id: 333, name: 'handler333'}]

      it 'should respond to modelChanged', inject (XmlImportHandler)->
          handler3 = new XmlImportHandler
            id: 333
            name: 'handler333'
          $scope.kwargs =
            page: 1
          response =
            pages: 2
            has_next: true
          response[handler.API_FIELDNAME + 's'] = [handler3]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?page=1&show=id,name,page"
          .respond 200, angular.toJson(response)
          $scope.$emit 'modelChanged'
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [{id: 333, name: 'handler333'}]

      it 'should respond to BaseListCtrl:start:load', inject (XmlImportHandler)->
          $scope.$emit.calls.reset()
          $scope.kwargs =
            page: 4
          handler4 = new XmlImportHandler
            id: 444
            name: 'handler444'
          response = {}
          response[handler.API_FIELDNAME + 's'] = [handler4]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?page=4&show=id,name,page"
          .respond 200, angular.toJson(response)
          $scope.$emit 'BaseListCtrl:start:load', 'noname'
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [{id: 444, name: 'handler444'}]
          expect($scope.$emit).toHaveBeenCalledWith 'BaseListCtrl:load:success', $scope.objects

      it 'should handle filter_opts changes', inject (XmlImportHandler)->
          handler4 = new XmlImportHandler
            id: 444
            name: 'handler444'
          response = {}
          response[handler.API_FIELDNAME + 's'] = [handler4]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?show=id,name&zinger=zaza"
          .respond 200, angular.toJson(response)
          $scope.filter_opts = {zinger: 'zaza'}
          $scope.$digest()
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [{id: 444, name: 'handler444'}]
          expect($scope.$emit).toHaveBeenCalledWith 'BaseListCtrl:load:success', $scope.objects

      it "should sort list", inject (XmlImportHandler) ->
          # loadMore concats objects
          handler1 = new XmlImportHandler
            id: 11
            name: 'handler11'
          handler2 = new XmlImportHandler
            id: 22
            name: 'handler22'
          $scope.kwargs =
            page: 1
            sort_by: 'updated_on'
            order: 'desc'
          response =
            pages: 1
            has_next: false
          response[handler.API_FIELDNAME + 's'] = [handler1, handler2]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?order=asc&page=1&show=id,name,page,sort_by,order&sort_by=name"
          .respond 200, angular.toJson(response)
          $scope.sort_list('name')
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [
            {id: 11, name: 'handler11'}
            {id: 22, name: 'handler22'}
          ]
          expect($scope.sort_by).toEqual('name')
          expect($scope.asc_order).toBe true

          # sort again (should change order to desc)
          response =
            pages: 1
            has_next: false
          response[handler.API_FIELDNAME + 's'] = [handler2, handler1]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?order=desc&page=1&show=id,name,page,sort_by,order&sort_by=name"
          .respond 200, angular.toJson(response)
          $scope.sort_list('name')
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [
            {id: 22, name: 'handler22'}
            {id: 11, name: 'handler11'}
          ]
          expect($scope.sort_by).toEqual('name')
          expect($scope.asc_order).toBe false

          # sort again by another field (should change order to asc)
          response =
            pages: 1
            has_next: false
          response[handler.API_FIELDNAME + 's'] = [handler1, handler2]
          $httpBackend.expectGET "#{handler.BASE_API_URL}?order=asc&page=1&show=id,name,page,sort_by,order&sort_by=id"
          .respond 200, angular.toJson(response)
          $scope.sort_list('id')
          $httpBackend.flush()
          expect(({id: x.id, name: x.name} for x in $scope.objects)).toEqual [
            {id: 11, name: 'handler11'}
            {id: 22, name: 'handler22'}
          ]
          expect($scope.sort_by).toEqual('id')
          expect($scope.asc_order).toBe true
