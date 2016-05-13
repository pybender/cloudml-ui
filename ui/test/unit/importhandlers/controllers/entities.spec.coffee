describe 'xml_importhandlers/controllers/entities', ->
  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.importhandlers.xml.controllers.entities'

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


  describe "EntitiesTreeCtrl", ->
    it "Should init scope and watch for entities update",
      inject (XmlImportHandler, Entity) ->
        handler = new XmlImportHandler
          id: 999
          name: 'import handler'
        url = "#{handler.BASE_API_URL}#{handler.id}"
        createController "EntitiesTreeCtrl"

        $scope.init handler
        expect($scope.handler.name).toEqual handler.name

        $scope.$digest() # to trigger the watch
        expect($scope.objects).toBe undefined
        # watch
        entity = new Entity
          id: 222
          name: 'entity 22'
          import_handler_id: 999
        handler.entity = entity
        $scope.$digest() # to trigger the watch
        expect($scope.objects).toEqual entity

        expect($scope.query_msg).toEqual {}

        $scope.load = jasmine.createSpy '$scope.load'
        $scope.$emit 'BaseListCtrl:start:load', 'entities'
        expect($scope.load).toHaveBeenCalled

    it "Should load entities",
      inject (XmlImportHandler) ->
        handler = new XmlImportHandler
          id: 999
          name: 'import handler'
        url = "#{handler.BASE_API_URL}#{handler.id}/?show=entities"
        createController "EntitiesTreeCtrl"
        $scope.init handler
        $scope.$emit 'BaseListCtrl:start:load', 'entities'
        $httpBackend.expectGET(url).respond 200, angular.toJson
          entities: [
            id: 22
            name: 'bb'
          ]
        $httpBackend.flush()

        $scope.setError = jasmine.createSpy '$scope.setError'
        $httpBackend.expectGET(url).respond 400
        $scope.load()
        $httpBackend.flush()
        expect($scope.setError).toHaveBeenCalled

    it "Should call open dialog for add entity",
      inject (Entity) ->
        entity = new Entity
          id: 222
          import_handler_id: 999
        createController "EntitiesTreeCtrl"
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $scope.addEntity entity
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Entity
          template: 'partials/importhandlers/xml/entities/edit.html'
          ctrlName: 'ModelEditDialogCtrl'
          list_model_name: 'entities'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for add field",
      inject (Field) ->
        field = new Field
          entity_id: 222
          import_handler_id: 999
        createController "EntitiesTreeCtrl"
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $scope.addField field
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Field
          template: 'partials/importhandlers/xml/fields/edit.html'
          ctrlName: 'ModelWithParamsEditDialogCtrl'
          list_model_name: 'entities'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for delete entity",
      inject (Entity) ->
        entity = new Entity
          id: 222
          import_handler_id: 999
        createController "EntitiesTreeCtrl"
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $scope.delete entity
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: entity
          template: 'partials/base/delete_dialog.html'
          ctrlName: 'DialogCtrl'
          list_model_name: "entities"
          action: 'delete'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for edit datasource",
      inject (Entity) ->
        entity = new Entity
          id: 222
          import_handler_id: 999
          name: "name"
          datasource_id: 666
          transformed_field_id: 777
          entity_id: 333
        createController "EntitiesTreeCtrl"
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $scope.editDataSource entity
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Entity
          template: 'partials/importhandlers/xml/entities/edit_datasource.html'
          ctrlName: 'ModelEditDialogCtrl'
          list_model_name: "entities"
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should save query text or set error",
      inject (XmlImportHandler, XmlQuery) ->
        query = new XmlQuery
          id: 999
          import_handler_id: 222
          entity_id: 333
        handler = new XmlImportHandler
          id: 222
          name: "handler"
        handler.query = query
        url = "#{settings.apiUrl}xml_import_handlers/#{query.import_handler_id}/entities/#{query.entity_id}/queries/#{query.id}/"
        createController "EntitiesTreeCtrl"
        $scope.handler = handler

        # no query text
        $scope.saveQueryText $scope.handler.query
        expect($scope.handler.query.edit_err).toEqual 'Please enter the query text'

        # save query text
        $scope.handler.query.text = 'some query'
        $scope.saveQueryText $scope.handler.query
        $httpBackend.expectPUT(url).respond 200, angular.toJson
          query:
            id: 999
            text: 'query'
            handler_id: 222
            entity_id: 333
        $httpBackend.flush()
        expect($scope.handler.query.msg).toEqual 'Query has been saved'
        expect($scope.handler.query.edit_err).toBe null

    it "Should call open dialog for runQuery with proper arguments",
      inject (XmlImportHandler, XmlQuery)->
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        handler = new XmlImportHandler
          id: 999
          name: 'import handelr'
        query = new XmlQuery
          id: 888

        url = "#{handler.BASE_API_URL}#{handler.id}"

        $rootScope.handler = handler
        createController "EntitiesTreeCtrl"

        $scope.runQuery query
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: null
          template: 'partials/importhandlers/test_query.html'
          ctrlName: 'QueryTestDialogCtrl'
          extra:
            handlerUrl: url
            datasources: handler.xml_data_sources
            query: query
          action: 'test xml import handler query'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for add sqoop",
      inject (Sqoop) ->
        sqoop = new Sqoop
          id: 222
          import_handler_id: 999
        createController "EntitiesTreeCtrl"
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        $scope.addSqoop sqoop
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Sqoop
          template: 'partials/importhandlers/xml/sqoop/edit.html'
          ctrlName: 'ModelEditDialogCtrl'
          list_model_name: "entities"
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for getting pig fields with proper args",
      inject (XmlImportHandler, Sqoop)->
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        handler = new XmlImportHandler
          id: 999
          name: 'import handelr'
        sqoop = new Sqoop
          id: 888

        $rootScope.handler = handler
        createController "EntitiesTreeCtrl"

        $scope.getPigFields sqoop
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: sqoop
          template: 'partials/importhandlers/xml/sqoop/load_pig_fields.html'
          ctrlName: 'PigFieldsLoader'
          extra: {noInput: false, title: 'Pig Fields'}

        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should save entity fields or set error",
      inject (Entity, XmlImportHandler) ->
        $rootScope.setError = jasmine.createSpy '$rootScope.setError'
        $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
        entity = new Entity
          id: 999
          import_handler_id: 222
          autoload_fields: true
        handler = new XmlImportHandler
          id: 222
          name: "handler"
        url = "#{settings.apiUrl}xml_import_handlers/#{entity.import_handler_id}/entities/#{entity.id}/"
        createController "EntitiesTreeCtrl"
        $scope.handler = handler
        $scope.handler.entity = entity

        # no query text
        $httpBackend.expectPUT(url).respond 400
        $scope.saveModel $scope.handler.entity, 'autoload_fields'
        $httpBackend.flush()
        expect($rootScope.setError).toHaveBeenCalled
        expect($rootScope.resetError).toHaveBeenCalled

        # save query text
        $scope.saveModel $scope.handler.entity, 'autoload_fields'
        $httpBackend.expectPUT(url).respond 200, angular.toJson
          entity:
            id: 999
            autoload_fields: true
            import_handler_id: 222
        $httpBackend.flush()
        expect($scope.handler.entity.autoload_fields).toBe true
        expect($rootScope.resetError).toHaveBeenCalled


  describe "PigFieldsLoader", ->
    it "Should request pig query generation for sqoop script",
      inject (XmlImportHandler, Sqoop)->
        sqoop = new Sqoop
          id: 888
          import_handler_id: 999
          entity_id: 555
        openOptions = {'model': sqoop}
        createController "PigFieldsLoader", {'openOptions': openOptions}
        $scope.getFields()

        url = Sqoop.$get_api_url({}, sqoop)
        $httpBackend.expectPUT "#{url}#{sqoop.id}/action/pig_fields/"
        .respond 200, angular.toJson {'fields': {}, 'sample': 'pig_data', 'sql': 'sql...'}
        $httpBackend.flush()
