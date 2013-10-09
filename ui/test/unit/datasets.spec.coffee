'use strict'

# jasmine specs for datasets

describe "datasets", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.datasets.model")

  beforeEach(module "app.datasets.model")
  beforeEach(module "app.datasets.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $window = null
  $dialog = null
  createController = null

  HANDLER_ID = '522333333344445d26c73315'
  DS_ID = '52231c7c07dbec2d26c73315'

  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $window = $injector.get('$window')
    $dialog = $injector.get('$dialog')

    spyOn($window.location, 'replace')

    BASE_URL = settings.apiUrl + 'importhandlers/' + HANDLER_ID + '/datasets/'

    createController = (ctrl) ->
       $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "DatasetListCtrl", ->

    it "should make no query", inject () ->
      createController "DatasetListCtrl"

  describe "DatasetActionsCtrl", ->

    it "should make no query", inject () ->
      createController "DatasetActionsCtrl"

    it "should open delete dialog", inject (ImportHandler, DataSet) ->
      $rootScope.handler = new ImportHandler()
      $rootScope.ds = new DataSet()

      $rootScope.openDialog = jasmine.createSpy()

      createController "DatasetActionsCtrl"
      $rootScope.delete()

      expect($rootScope.openDialog).toHaveBeenCalled()

    it "should generate download link", inject (ImportHandler, DataSet) ->
      $rootScope.handler = new ImportHandler({_id: HANDLER_ID})
      $rootScope.ds = new DataSet(
        {_id: DS_ID, on_s3: true, import_handler_id: HANDLER_ID}
      )

      url = BASE_URL + DS_ID + '/action/generate_url/?'
      $httpBackend.expectGET(url).respond('{"url": "http://amazon/ds_path"}')

      createController "DatasetActionsCtrl"
      $rootScope.download()
      $httpBackend.flush()

      expect($window.location.replace).toHaveBeenCalledWith('http://amazon/ds_path')

  describe "DataSetDetailsCtrl", ->

    it "should init sections", inject () ->
      $routeParams.handler_id = HANDLER_ID
      $routeParams.id = DS_ID

      $rootScope.initSections = jasmine.createSpy()

      createController "DataSetDetailsCtrl"
      expect($rootScope.initSections).toHaveBeenCalledWith(
        $rootScope.go, "model:details", simple=true
      )

    it "should make details query", inject () ->
      $routeParams.handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $rootScope.initSections = jasmine.createSpy()

      url = BASE_URL + DS_ID + '/?show=' + encodeURIComponent('name,status,created_on,updated_on,data,
on_s3,import_params,error,filesize,records_count,
time,created_by,import_handler_id')
      $httpBackend.expectGET(url).respond('{"dataset": {"name": "Some name"}}')

      createController "DataSetDetailsCtrl"
      $rootScope.go()
      $httpBackend.flush()

      expect($rootScope.dataset).toBeDefined()
      expect($rootScope.dataset.name).toBe('Some name')

  describe "DatasetSelectCtrl", ->

    it "should make list query", inject () ->
      url = BASE_URL + '?handler_id=' + HANDLER_ID + '&show=' +
      encodeURIComponent('name,_id') + '&status=Imported'
      $httpBackend.expectGET(url).respond('{"datasets": [{"name": "Some name", "_id": "'+ DS_ID + '"}]}')

      $rootScope.handler = {
        _id: HANDLER_ID
      }
      $rootScope.activateSectionColumn = jasmine.createSpy()

      createController "DatasetSelectCtrl"
      $httpBackend.flush()

      expect($rootScope.datasets[0]._id).toEqual('')
      expect($rootScope.datasets[1]._id).toEqual(DS_ID)
      expect($rootScope.datasets[1].name).toEqual('Some name')
      expect($rootScope.activateSectionColumn).toHaveBeenCalledWith('dataset', undefined )

  # TODO: solve the "Unknown provider: dialogProvider" issue and test
  xdescribe "LoadDataDialogCtrl", ->

    it "should make no query", inject () ->
      createController "LoadDataDialogCtrl"
