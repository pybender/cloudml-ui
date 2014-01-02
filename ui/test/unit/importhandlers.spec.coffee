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

    createController = (ctrl) ->
       $controller(ctrl, {'$scope' : $rootScope })
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

      url = BASE_URL + HANDLER_ID + '/?show=' + encodeURIComponent('name,_id,import_params,
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

    it "should open import dialog", inject () ->
      createController "ImportHandlerActionsCtrl"
      $rootScope.openDialog = jasmine.createSpy()

      $rootScope.importData({_id: HANDLER_ID})

      expect($rootScope.openDialog).toHaveBeenCalledWith(
        jasmine.any(Object),
        {_id: HANDLER_ID},
        'partials/import_handler/load_data.html',
        'LoadDataDialogCtrl'
      )

    it "should open delete dialog", inject () ->
      createController "ImportHandlerActionsCtrl"
      $rootScope.openDialog = jasmine.createSpy()

      $rootScope.delete({_id: HANDLER_ID})

      expect($rootScope.openDialog).toHaveBeenCalledWith(
        jasmine.any(Object),
        {_id: HANDLER_ID},
        'partials/base/delete_dialog.html',
        'DeleteImportHandlerCtrl',
        jasmine.any(String), jasmine.any(String), jasmine.any(String)
      )

  describe "ImportHandlerSelectCtrl", ->

    it "should make list query", inject () ->
      url = BASE_URL + '?show=name'
      $httpBackend.expectGET(url).respond('{"import_handlers": [{"_id": "' + HANDLER_ID + '", "name": "Some Name"
}]}')

      createController "ImportHandlerSelectCtrl"
      $httpBackend.flush()

      expect($rootScope.handlers.length).toBe(1)
      expect($rootScope.handlers_list[0].value).toBe(HANDLER_ID)
      expect($rootScope.handlers_list[0].text).toBe("Some Name")
