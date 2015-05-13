'use strict'

describe "app.importhandlers.controllers", ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.model'
    module 'app.importhandlers.controllers'
    module 'app.xml_importhandlers.models'
    module 'app.xml_importhandlers.controllers'
    module 'app.xml_importhandlers.controllers.entities'
    module 'app.models.model'
    module 'app.datasets.model'
    module 'app.features.models'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $modal = null
  createController = null
  $scope = null
  $timeout = null
  $window = null

  HANDLER_ID = '522333333344445d26c73315'

  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $modal = $injector.get('$modal')
    $timeout = $injector.get('$timeout')
    $window = $injector.get('$window')

#    spyOn($location, 'path')
#    spyOn($location, 'search')

    BASE_URL = settings.apiUrl + 'importhandlers/'

    $scope = $rootScope.$new()
    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "ImportHandlerListCtrl", ->

    it "should make no query", inject (ImportHandler) ->
      createController "ImportHandlerListCtrl"

      expect($scope.MODEL).toEqual ImportHandler
      expect($scope.FIELDS).toEqual ImportHandler.MAIN_FIELDS
      expect($scope.ACTION).toEqual 'loading handler list'


  describe "ImportHandlerDetailsCtrl", ->

    prepareContext = null
    testHandlerId = 999
    beforeEach inject (ImportHandler)->
      prepareContext = ->
        $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $routeParams = {id: testHandlerId}
        createController 'ImportHandlerDetailsCtrl',
          $rootScope: $rootScope
          $routeParams: $routeParams
          ImportHandler: ImportHandler

        expect($scope.handler.id).toEqual testHandlerId
        expect($scope.LOADED_SECTIONS).toEqual []
        expect($scope.PROCESS_STRATEGIES).toEqual [ 'boolean', 'composite', 'float', 'identity', 'integer', 'json', 'string' ]
        expect($rootScope.initSections).toHaveBeenCalledWith($scope.go)
        $scope.setError = jasmine.createSpy '$scope.setError'

    it 'should throw error if no routeParams id', inject (ImportHandler) ->
      $routeParams = {}

      expect ->
        createController "ImportHandlerDetailsCtrl",
          $rootScope: $rootScope
          $routeParams: $routeParams
          ImportHandler: ImportHandler
      .toThrow new Error 'Can\'t initialize without import handler id'

    it 'should go and load main section', inject (ImportHandler)->
      prepareContext()

      expect($rootScope.initSections).toHaveBeenCalledWith($scope.go)

      # handling errors first
      $httpBackend.expectGET "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/?show=#{ImportHandler.MAIN_FIELDS},data,crc32"
      .respond 400

      $scope.go ['main']
      $httpBackend.flush()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading handler details'
      expect($scope.LOADED_SECTIONS).toEqual []

      # good http loading
      response = {}
      response[$scope.handler.API_FIELDNAME] = $scope.handler
      $httpBackend.expectGET "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/?show=#{ImportHandler.MAIN_FIELDS},data,crc32"
      .respond 200, angular.toJson(response)

      $scope.go ['main']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['main']

      # another go should not trigger anything
      $scope.go ['main']
      expect($scope.LOADED_SECTIONS).toEqual ['main']

    it 'should broadcast dataset loading', inject (ImportHandler)->
      prepareContext()

      $scope.$broadcast = jasmine.createSpy '$scope.$broadcast'

      response = {}
      response[$scope.handler.API_FIELDNAME] = $scope.handler
      $httpBackend.expectGET "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/?show=#{ImportHandler.MAIN_FIELDS},data,crc32"
      .respond 200, angular.toJson(response)

      $scope.go ['dataset']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['dataset']
      expect($scope.$broadcast).toHaveBeenCalledWith 'loadDataSet', true

      # another go should not trigger anything
      $scope.go ['dataset']
      expect($scope.LOADED_SECTIONS).toEqual ['dataset']

    it 'should save handler and handle any errors, also saving data only', ->
      prepareContext()

      # $scope.save case
      response = {}
      response[$scope.handler.API_FIELDNAME] = $scope.handler
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 200, angular.toJson(response)

      $scope.save ['some','fields']
      $httpBackend.flush()

      # error while saving
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400
      $scope.save ['some','fields']
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'saving import handler'

      # $scope.saveData case
      response = {}
      response[$scope.handler.API_FIELDNAME] = $scope.handler
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 200, angular.toJson(response)

      $scope.saveData()
      $httpBackend.flush()

      # error while saving
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400
      $scope.saveData()
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'saving handler details'

    it 'should handle making and item required, along with errors', inject (Item)->
      prepareContext()

      item = new Item
        id: '888'
        name: 'item_name'
        handler: $scope.handler
      response = {}
      response[$scope.handler.API_FIELDNAME] = $scope.handler
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 200, angular.toJson(response)

      $scope.makeRequired item, true
      $httpBackend.flush()

      # an error while saving
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400

      $scope.makeRequired item, true
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error toggling required on query item'


    testDeleteSomethingFromList = (thing1, thing2, thing3, deleteFn)->
      ###
      This is used to test delete query, delete item and delete feature.
      It doesn't test deletion errors
      ###
      testDelete = (something, expectationsFn)->
        response = {}
        response[$scope.handler.API_FIELDNAME] = $scope.handler
        $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
        .respond 200, angular.toJson(response)

        deleteFn things, something
        $httpBackend.flush()

        expectationsFn()

      [thing1.num, thing2.num, thing3.num] = [0, 1, 2]
      things = [thing1, thing2, thing3]
      testDelete thing2, ->
        expect(things).toEqual [thing1, thing3]
        expect(thing1.num).toBe 0
        expect(thing3.num).toBe 1

      [thing1.num, thing2.num, thing3.num] = [0, 1, 2]
      things = [thing1, thing2, thing3]
      testDelete thing1, ->
        expect(things).toEqual [thing2, thing3]
        expect(thing2.num).toBe 0
        expect(thing3.num).toBe 1

      [thing1.num, thing2.num, thing3.num] = [0, 1, 2]
      things = [thing1, thing2, thing3]
      testDelete thing3, ->
        expect(things).toEqual [thing1, thing2]
        expect(thing1.num).toBe 0
        expect(thing2.num).toBe 1

    it 'should handle delete query with handling any errors', inject (Query)->
      prepareContext()

      query1 = new Query
        id: '888'
        name: 'query1'
        handler: $scope.handler
        num: 0

      query2 = new Query
        id: '777'
        name: 'query2'
        handler: $scope.handler
        num: 1

      query3 = new Query
        id: '666'
        name: 'query3'
        handler: $scope.handler
        num: 2

      testDeleteSomethingFromList query1, query2, query3, $scope.deleteQuery

      # an error while deleting query
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400

      $scope.deleteQuery [query1, query2, query3], query2
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error deleting query'

    it 'should handle delete item with handling any errors', inject (Item)->
      prepareContext()

      item1 = new Item
        id: '888'
        name: 'item1'
        handler: $scope.handler
        num: 0

      item2 = new Item
        id: '777'
        name: 'item2'
        handler: $scope.handler
        num: 1

      item3 = new Item
        id: '666'
        name: 'item3'
        handler: $scope.handler
        num: 2

      testDeleteSomethingFromList item1, item2, item3, $scope.deleteItem

      # an error while deleting item
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400

      $scope.deleteItem [item1, item2, item3], item2
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error deleting item'

    it 'should handle delete feature with handling any errors', inject (TargetFeature)->
      prepareContext()

      feature1 = new TargetFeature
        id: '888'
        name: 'feature1'
        handler: $scope.handler
        num: 0
        feature_set_id: 111

      feature2 = new TargetFeature
        id: '777'
        name: 'feature2'
        handler: $scope.handler
        num: 1
        feature_set_id: 111

      feature3 = new TargetFeature
        id: '666'
        name: 'feature3'
        handler: $scope.handler
        num: 2
        feature_set_id: 111

      testDeleteSomethingFromList feature1, feature2, feature3, $scope.deleteFeature

      # an error while deleting feature
      $httpBackend.expectPUT "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}/"
      .respond 400

      $scope.deleteFeature [feature1, feature2, feature3], feature2
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error deleting feature'

    it 'should call onto open dialog to edit datasource', ->

      prepareContext()

      $scope.editDataSource $scope.handler, {some: 'dataset'}

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: null
        template: 'partials/import_handler/datasource/edit_handler_datasource.html'
        ctrlName: 'DataSourceEditDialogCtrl'
        action: 'add data source'
        extra: {handler: $scope.handler, ds: {some: 'dataset'}}
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should call onto open dialog to edit target feature',
      inject (TargetFeature, Item)->

        prepareContext()

        item = new Item
          id: '777'
          name: 'item2'
          handler: $scope.handler
          num: 1

        feature = new TargetFeature
          id: '888'
          name: 'feature1'
          handler: $scope.handler
          num: 0
          feature_set_id: 111

        $scope.editTargetFeature item, feature

        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: null
          template: 'partials/import_handler/edit_target_feature.html'
          ctrlName: 'TargetFeatureEditDialogCtrl'
          extra: {handler: item.handler, feature: feature, item: item}
          action: 'edit target feature'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should call onto open dialog to run query', inject (Query)->

      prepareContext()

      query = new Query
        id: '777'
        name: 'item2'
        handler: $scope.handler
        num: 1

      $scope.runQuery query

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: null
        template: 'partials/import_handler/test_query.html'
        ctrlName: 'QueryTestDialogCtrl'
        extra:
          handlerUrl: $scope.handler.getUrl()
          datasources: $scope.handler.datasource,
          query: query
        action: 'test import handler query'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe "QueryTestDialogCtrl and run query", ->

    it "should initialize scope and run queries", ->
      handler = getXmlHandler()
      query = getXmlQuery()

      $rootScope.$close = jasmine.createSpy '$rootScope.$close'
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'some error'
      openOptions =
        extra:
          handlerUrl: "#{settings.apiUrl}xml_import_handlers/#{handler.id}"
          datasources: handler.xml_data_sources
          query: query
      createController "QueryTestDialogCtrl", {'openOptions': openOptions}

      expect($scope.query).toEqual query
      expect($scope.params).toEqual ['start', 'end']
      expect($scope.query.test_params).toEqual {}
      expect($scope.query.test_limit).toEqual 2
      expect($scope.query.test_datasource).toEqual handler.xml_data_sources[0].name
      expect($scope.runQuery).toBeDefined()
      expect($scope.datasources.length).toEqual 1
      expect($scope.datasources[0].type).toEqual 'db'

      url = "#{settings.apiUrl}xml_import_handlers/#{handler.id}/action/run_sql/"
      $httpBackend.expectPUT(url).respond('{"import_handlers": [{"id": "' + handler.id + '", "name": "Some Name"}]}')

      $scope.runQuery()
      $httpBackend.flush()

      expect($rootScope.$close).toHaveBeenCalled()
      expect($scope.query.test.error).toBeUndefined()

      # handles errors
      url = "#{settings.apiUrl}xml_import_handlers/#{handler.id}/action/run_sql/"
      $httpBackend.expectPUT(url).respond 400

      $scope.runQuery()
      $httpBackend.flush()
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'testing sql query'
      expect($scope.query.test.error).toEqual 'some error'


  describe 'ImportTestDialogCtrl', ->

    it 'should init scope, run test import and handle errors', inject (ImportHandler)->

      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'
      $window = {location: {replace: jasmine.createSpy '$window.location.replace'}}

      handler = new ImportHandler
        id: 999
        name: 'imoprt handler 999'
        import_params: [{param: 'parameter1'}, {param: 'parameter2'}]

      openOptions = {extra: {handler: handler}}
      createController 'ImportTestDialogCtrl', {openOptions: openOptions, $window: $window}

      expect($scope.handler).toEqual handler
      expect($scope.params).toEqual openOptions.extra.handler.import_params
      expect($scope.parameters).toEqual {}
      expect($scope.test_limit).toEqual jasmine.any(Number)
      expect($scope.err).toEqual ''

      $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/action/test_handler/"
      .respond 200, angular.toJson {url: 'http://www.some.new/url'}
      $scope.runTestImport()
      $httpBackend.flush()

      expect($window.location.replace).toHaveBeenCalledWith 'http://www.some.new/url'
      expect($rootScope.$close).toHaveBeenCalled()

      # error handling
      $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/action/test_handler/"
      .respond 400
      $scope.runTestImport()
      $httpBackend.flush()

      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'testing import handler'
      expect($scope.err).toEqual 'an error'


  describe 'TargetFeatureEditDialogCtrl', ->

    handler = null
    feature = null
    item = null
    prepareContext = (withFeature)->
      inject (ImportHandler, TargetFeature, Item)->
        handler = null
        feature = null
        item = null

        $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'
        $rootScope.$close = jasmine.createSpy '$rootScope.$close'

        handler = new ImportHandler
          id: 999
          name: 'imoprt handler 999'
          import_params: [{param: 'parameter1'}, {param: 'parameter2'}]

        if withFeature
          feature = new TargetFeature
            id: '888'
            name: 'feature1'
            handler: handler
            num: -1
            feature_set_id: 111

        item = new Item
          id: '777'
          name: 'item2'
          handler: $scope.handler
          num: 1
          process_as: ['json']
          target_features: []
          query_num: 8989

        openOptions = {extra: {handler: handler, item: item}}
        if withFeature
          openOptions.extra.feature = feature
        createController 'TargetFeatureEditDialogCtrl', {openOptions: openOptions, $window: $window}

    it 'should init scope and watch event with feature supplied', ->
      prepareContext(true)

      expect($scope.handler).toEqual handler
      expect($scope.model).toEqual feature
      expect($scope.item).toEqual item
      expect($scope.DONT_REDIRECT).toBe true
      expect($scope.fields).toEqual ['name'].concat EXTRA_TARGET_FEATURES_PARAMS[item.process_as]
      expect($scope.readabilityTypes).toBe READABILITY_TYPES

      # trigger event
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($rootScope.$close).toHaveBeenCalled()
      expect($scope.model.num).toEqual 0
      expect($scope.item.target_features).toEqual [feature]

    it 'should init scope and watch event with not feature supplied', inject (TargetFeature)->
      prepareContext(false)

      expect($scope.handler).toEqual handler
      expect($scope.item).toEqual item
      expect($scope.DONT_REDIRECT).toBe true
      expect($scope.fields).toEqual ['name'].concat EXTRA_TARGET_FEATURES_PARAMS[item.process_as]
      expect($scope.readabilityTypes).toBe READABILITY_TYPES
      expect($scope.model).toEqual jasmine.any(TargetFeature)
      expect($scope.model.query_num).toEqual item.query_num
      expect($scope.model.item_num).toEqual item.num

      # trigger event
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($rootScope.$close).toHaveBeenCalled()
      expect($scope.model.num).toEqual 0
      expect($scope.item.target_features).toEqual [$scope.model]


  describe "AddImportHandlerCtl", ->

    it "should initialize empty model", inject (ImportHandler) ->
      createController "AddImportHandlerCtl", {ImportHandler: ImportHandler}
      expect($scope.types).toEqual [{name: 'Db'}, {name: 'Request'}]
      expect($scope.model).toEqual jasmine.any(ImportHandler)

  describe "DeleteImportHandlerCtrl", ->

    it "should load models and errors", inject ($location, Model) ->
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

      openOptions =
        action: 'some action'
        model: {some: 'model'}
        path: 'some/path'
        ownerScope: {some: 'owner_scope'}

      models = [
        new Model
          id: 99
          name: 'attached model'
      ]
      response = {}
      response[models[0].API_FIELDNAME + 's'] = models
      $httpBackend.expectGET "#{models[0].BASE_API_URL}action/by_importhandler/?show=name,id"
      .respond 200, angular.toJson(response)
      createController 'DeleteImportHandlerCtrl', {$location: $location, Model: Model, openOptions}
      $httpBackend.flush()

      expect($rootScope.resetError).toHaveBeenCalled()
      expect($scope.MESSAGE).toEqual openOptions.action
      expect($scope.model).toEqual openOptions.model
      expect($scope.path).toEqual openOptions.path
      expect($scope.action).toEqual openOptions.action
      expect($scope.extra_template).toEqual 'partials/import_handler/extra_delete.html'
      expect(({id: x.id, name: x.name} for x in $scope.umodels)).toEqual [{name: 'attached model', id: 99}]

      # error handling
      $httpBackend.expectGET "#{models[0].BASE_API_URL}action/by_importhandler/?show=name,id"
      .respond 400
      createController 'DeleteImportHandlerCtrl', {$location: $location, Model: Model, openOptions}
      $httpBackend.flush()
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'loading models that use import handler'


  describe "ImportHandlerActionsCtrl", ->

    it "should make no query", ->
      createController "ImportHandlerActionsCtrl"

    it "should open import dialog", ->
      $rootScope.openDialog = jasmine.createSpy('$scope.openDialog')
      createController "ImportHandlerActionsCtrl"

      $scope.importData({id: HANDLER_ID})

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model:
          id: HANDLER_ID
        template: 'partials/import_handler/load_data.html'
        ctrlName: 'LoadDataDialogCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "should open delete dialog", ->
      $rootScope.openDialog = jasmine.createSpy('$scope.openDialog')
      createController "ImportHandlerActionsCtrl"

      $scope.delete({id: HANDLER_ID, TYPE: 'json'})

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model:
          id: HANDLER_ID
          TYPE: 'json'
        template: 'partials/base/delete_dialog.html',
        ctrlName: 'DeleteImportHandlerCtrl'
        action: 'delete import handler'
        path : '/handlers/json'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "should open test handler dialog", ->
      $rootScope.openDialog = jasmine.createSpy('$scope.openDialog')
      createController "ImportHandlerActionsCtrl"

      $scope.handler = {id: HANDLER_ID, TYPE: 'json'}
      $scope.testHandler()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        template: 'partials/import_handler/test_handler.html'
        ctrlName: 'ImportTestDialogCtrl'
        action: 'test import handler'
        extra: {handler: $scope.handler}
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "should open upload to predict dialog", ->
      $rootScope.openDialog = jasmine.createSpy('$scope.openDialog')
      createController "ImportHandlerActionsCtrl"

      $scope.uploadHandlerToPredict({some: 'model'})

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'model'}
        template: 'partials/servers/choose.html'
        ctrlName: 'ImportHandlerUploadToServerCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'ImportHandlerUploadToServerCtrl', ->

    it 'should init scope and upload with handling errors', inject (ImportHandler)->
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'
      $rootScope.setError = jasmine.createSpy('$rootScope.resetError').and.returnValue 'an error for upload'

      handler = new ImportHandler
        id: 999
        name: 'some import handler 999'
      openOptions = {model: handler}

      createController 'ImportHandlerUploadToServerCtrl', {$rootScope: $rootScope, openOptions: openOptions}

      expect($rootScope.resetError).toHaveBeenCalled()
      expect($scope.model).toEqual openOptions.model
      expect($scope.model.server).toBe null

      response = {status: 'hello world'}
      $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/action/upload_to_server/"
      .respond 200, angular.toJson(response)
      $scope.upload()
      $httpBackend.flush()

      expect($rootScope.msg).toEqual 'hello world'

      # error handling
      $httpBackend.expectPUT "#{handler.BASE_API_URL}#{handler.id}/action/upload_to_server/"
      .respond 400
      $scope.upload()
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error uploading to predict'
      expect($rootScope.msg).toEqual 'an error for upload'


  describe "ImportHandlerSelectCtrl", ->

    it "should make list query", inject () ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

      url = settings.apiUrl + 'any_importhandlers/' + '?show=name,type,id'
      HANDLER_ID_XML = '123321'
      $httpBackend.expectGET(url).respond(
        '{"import_handler_for_any_types": [{"id": "' + HANDLER_ID_XML + '", "name": "Z Some Name", "type": "xml"}, {"id": "' + HANDLER_ID + '", "name": "J Some Name", "type": "json"}]}')

      createController "ImportHandlerSelectCtrl"
      $httpBackend.flush()

      expect($scope.handlers_list[1].value).toBe(HANDLER_ID_XML+'xml')
      expect($scope.handlers_list[1].text).toBe("Z Some Name(xml)")
      expect($scope.handlers_list[0].value).toBe(HANDLER_ID + 'json')
      expect($scope.handlers_list[0].text).toBe("J Some Name(json)")

      # error handling
      $httpBackend.expectGET(url).respond 400
      createController "ImportHandlerSelectCtrl"
      $httpBackend.flush()
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'loading import handler list'

  describe 'AddImportHandlerQueryCtrl', ->

    it 'initialize scope and respond to event', ->

      $routeParams = {}
      expect(->
        createController 'AddImportHandlerQueryCtrl', {$routeParams: $routeParams, $location: $location}
      ).toThrow new Error 'Specify id'

      $routeParams = {id: 123}
      createController 'AddImportHandlerQueryCtrl', {$routeParams: $routeParams}

      expect($scope.handler.id).toEqual 123
      expect($scope.model.handler.id).toEqual 123
      expect($scope.model.num).toEqual -1

      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($location.path()).toEqual '/handlers/json/123'


  describe 'AddImportHandlerQueryItemCtrl', ->

    it 'AddImportHandlerQueryItemCtrl', ->

      $routeParams = {num: 1}
      expect(->
        createController 'AddImportHandlerQueryItemCtrl', {$routeParams: $routeParams}
      ).toThrow new Error 'Specify id'

      $routeParams = {id: 888}
      expect(->
        createController 'AddImportHandlerQueryItemCtrl', {$routeParams: $routeParams}
      ).toThrow new Error 'Specify query number'

      $routeParams = {id: 888, num: 1}
      createController 'AddImportHandlerQueryItemCtrl', {$routeParams: $routeParams}

      expect($scope.PROCESS_STRATEGIES).toEqual [ 'boolean', 'composite', 'float', 'identity', 'integer', 'json', 'string' ]
      expect($scope.handler.id).toEqual 888
      expect($scope.model.handler.id).toEqual 888
      expect($scope.model.query_num).toEqual 1
      expect($scope.model.num).toEqual -1

      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($location.path()).toEqual '/handlers/json/888'

  getXmlHandler = ->
    handler = null
    inject( (XmlImportHandler) ->
      handler = new XmlImportHandler()
      handler.loadFromJSON
        id: 110011
        xml_data_sources: [
          import_handler_id: 456654
          type: 'db'
          name: 'odw'
          id: 321
          params:
            host: 'localhost'
            password: 'cloudml'
            vendor: 'postgres'
            dbname: 'cloudml'
            user: 'cloudml'
        ,
          import_handler_id: 456654
          type: 'http'
          name: 'http'
          id: 321
          params:
            url: 'anything for now'
        ]
    )
    handler

  getXmlQuery = ->
    query = null
    inject( (XmlQuery)->
      queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '\#\{start\}' AND qi.file_provenance_date < '\#\{end\}'"
      query = new XmlQuery()
      query.loadFromJSON
        id: 123321
        text: queryText
        import_handler_id: 456654
        entity_id: 789987
    )
    query

  getJsonHandler = ->
    handler = null
    inject( (ImportHandler) ->
      handler = new ImportHandler()
      handler.loadFromJSON
        id: 220022
        datasource: [
          db:
              vendor: "postgres"
              conn: "host='localhost' dbname='cloudml' user='cloudml' password='cloudml'"
            type: "sql",
            name: "odw"
        ]
    )
    handler

  getJsonQuery = ->
    query = null
    inject( (Query)->
      queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s'"
      query = new Query()
      query.loadFromJSON
        id: 321123
    )
    query

