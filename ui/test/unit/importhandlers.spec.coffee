'use strict'

# jasmine specs for importhandlers

describe "importhandlers", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.importhandlers.controllers")
  beforeEach(module "app.xml_importhandlers.models")
  beforeEach(module "app.xml_importhandlers.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $dialog = null
  createController = null

  HANDLER_ID = '522333333344445d26c73315'

  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $dialog = $injector.get('$dialog')

    spyOn($location, 'path')
    spyOn($location, 'search')

    BASE_URL = settings.apiUrl + 'importhandlers/'

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $rootScope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "ImportHandlerListCtrl", ->

    it "should make no query", inject () ->
      createController "ImportHandlerListCtrl"

  describe "ImportHandlerDetailsCtrl", ->

    it "should init sections", inject () ->
      $routeParams.id = HANDLER_ID

      $rootScope.initSections = jasmine.createSpy()

      createController "ImportHandlerDetailsCtrl"
      expect($rootScope.initSections).toHaveBeenCalledWith($rootScope.go)

    it "should make details and save queries", inject () ->
      $routeParams.id = HANDLER_ID
      $rootScope.initSections = jasmine.createSpy()

      url = BASE_URL + HANDLER_ID + '/?show=' + encodeURIComponent('name,id,import_params,
created_on,created_by,error,data')
      $httpBackend.expectGET(url).respond('{"import_handler": {"name": "Some name"}}')

      createController "ImportHandlerDetailsCtrl"
      $rootScope.go(['section_name', ''])
      $httpBackend.flush()

      expect($rootScope.handler).toBeDefined()
      expect($rootScope.handler.name).toBe('Some name')

      $rootScope.handler.type = {'name': 'some'}

      url = BASE_URL + HANDLER_ID + '/?'
      $httpBackend.expectPUT(url).respond('{"import_handler": {"name": "Some name"}}')

      $rootScope.saveData()
      $httpBackend.flush()

  describe "AddImportHandlerCtl", ->

    it "should initialize empty model", inject () ->
      createController "AddImportHandlerCtl"
      expect($rootScope.types).toBeDefined()
      expect($rootScope.model).toBeDefined()

  # TODO: solve the "Unknown provider: dialogProvider" issue and test
  xdescribe "DeleteImportHandlerCtrl", ->

    it "should load models", inject () ->
      createController "DeleteImportHandlerCtrl"

  describe "ImportHandlerActionsCtrl", ->

    it "should make no query", inject () ->
      createController "ImportHandlerActionsCtrl"

    it "should open import dialog", inject ($dialog) ->
      createController "ImportHandlerActionsCtrl"
      $rootScope.openDialog = jasmine.createSpy('openDialogSpy')

      $rootScope.importData({id: HANDLER_ID})

      expect($rootScope.openDialog).toHaveBeenCalledWith(
        $dialog: $dialog
        model:
          id: HANDLER_ID
        template: 'partials/import_handler/load_data.html'
        ctrlName: 'LoadDataDialogCtrl'
      )

    it "should open delete dialog", inject ($dialog) ->
      createController "ImportHandlerActionsCtrl"
      $rootScope.openDialog = jasmine.createSpy()

      $rootScope.delete({id: HANDLER_ID, TYPE: 'json'})

      expect($rootScope.openDialog).toHaveBeenCalledWith(
        $dialog: $dialog
        model:
          id: HANDLER_ID
          TYPE: 'json'
        template: 'partials/base/delete_dialog.html',
        ctrlName: 'DeleteImportHandlerCtrl'
        action: 'delete import handler'
        path : '/handlers/json'
      )

  describe "ImportHandlerSelectCtrl", ->

    it "should make list query", inject () ->
      url = BASE_URL + '?show=name'
      xml_ih_url = settings.apiUrl + 'xml_import_handlers/' + '?show=name'
      HANDLER_ID_XML = '123321'
      $httpBackend.expectGET(url).respond('{"import_handlers": [{"id": "' + HANDLER_ID + '", "name": "Some Name"}]}')
      $httpBackend.expectGET(xml_ih_url).respond('{"xml_import_handlers": [{"id": "' + HANDLER_ID_XML + '", "name": "Some Name"}]}')

      createController "ImportHandlerSelectCtrl"
      $httpBackend.flush()

      expect($rootScope.handlers.length).toBe(1)
      expect($rootScope.handlers_list[0].value).toBe(HANDLER_ID)
      expect($rootScope.handlers_list[0].text).toBe("Some Name")
      expect($rootScope.handlers_list[1].value).toBe(HANDLER_ID_XML+'xml')
      expect($rootScope.handlers_list[1].text).toBe("Some Name(xml)")

  describe "XmlQuery", ->

    it "should properly parse parameters", inject((XmlQuery)->
      queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s'"
      query = new XmlQuery({text: queryText})
      expect(query).toBeDefined()
      expect(query.text).toEqual queryText
      params = query.getParams()
      expect(params).toEqual ['start', 'end']
    )

  describe "XmlQueryTestDialogCtrl and run query", ->

    it "should initialize scope",
      inject ($rootScope, $dialog, XmlQuery, XmlImportHandler, Entity)->
        queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s'"
        handler = new XmlImportHandler(
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
        ])
        query = new XmlQuery(
          id: 123321
          text: queryText
          import_handler_id: 456654
          entity_id: 789987
        )

        dialog =
          extra:
            handler: handler
            query: query
          close: jasmine.createSpy()
        createController "XmlQueryTestDialogCtrl", {'dialog': dialog}

        expect($rootScope.query).toEqual query
        expect($rootScope.params).toEqual ['start', 'end']
        expect($rootScope.dialog).toEqual dialog
        expect($rootScope.query.test_params).toEqual {}
        expect($rootScope.query.test_limit).toEqual 2
        expect($rootScope.query.test_datasource).toEqual handler.xml_data_sources[0].name
        expect($rootScope.runQuery).toBeDefined()

        url = "#{settings.apiUrl}xml_import_handlers/#{query.import_handler_id}/entities/#{query.entity_id}/queries/#{query.id}/action/run_sql/?"
        $httpBackend.expectPUT(url).respond('{"import_handlers": [{"id": "' + HANDLER_ID + '", "name": "Some Name"}]}')

        $rootScope.runQuery()
        $httpBackend.flush()

        expect(dialog.close).toHaveBeenCalled()
        expect($rootScope.query.test.error).toBeUndefined()
