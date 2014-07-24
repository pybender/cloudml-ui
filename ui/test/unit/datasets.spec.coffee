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
  beforeEach(module "app.xml_importhandlers.models")
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

    BASE_URL = settings.apiUrl + 'importhandlers/json/' + HANDLER_ID + '/datasets/'

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
      spyOn window, '$cml_window_location_replace'
      .andCallFake () -> null

      $rootScope.handler = new ImportHandler({id: HANDLER_ID})
      $rootScope.ds = new DataSet(
        {id: DS_ID, on_s3: true, import_handler_id: HANDLER_ID}
      )

      url = BASE_URL + DS_ID + '/action/generate_url/?'
      $httpBackend.expectGET(url).respond('{"url": "http://amazon/ds_path"}')

      createController "DatasetActionsCtrl"
      $rootScope.download()
      $httpBackend.flush()

      expect($cml_window_location_replace).toHaveBeenCalledWith('http://amazon/ds_path')

  describe "DataSetDetailsCtrl", ->

    it "should init sections", inject () ->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'

      $rootScope.initSections = jasmine.createSpy()

      createController "DataSetDetailsCtrl"
      expect($rootScope.initSections).toHaveBeenCalledWith(
        $rootScope.go, "model:details", simple=true
      )

    it "should make details query", inject (DataSet) ->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'
      $rootScope.initSections = jasmine.createSpy()

      url1 = BASE_URL + DS_ID + '/?show=' + encodeURIComponent(DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS)
      url2 = BASE_URL + DS_ID + '/action/sample_data/?size=15'
      $httpBackend.expectGET(url1).respond('{"data_set": {"name": "Some name"}}')
      $httpBackend.expectGET(url2).respond('[{"contractor.dev_skill_test_passed_count": "18", "contractor.dev_bill_rate": "5.56"}]')

      createController "DataSetDetailsCtrl"
      expect($rootScope.initSections).toHaveBeenCalledWith(
        $rootScope.go, "model:details", simple=true
      )

      $rootScope.go()
      $httpBackend.flush()

      expect($rootScope.dataset).toBeDefined()
      expect($rootScope.dataset.name).toBe('Some name')
      expect($rootScope.dataset.samples_json).toEqual angular.toJson([
        'contractor.dev_skill_test_passed_count': '18'
        'contractor.dev_bill_rate': '5.56'
      ], true)

  describe "DatasetSelectCtrl", ->

    it "should make list query", inject () ->
      url = settings.apiUrl + 'importhandlers/json/' + HANDLER_ID +
        '/datasets/?import_handler_id=522333333344445d26c73315&import_handler_type=json&show=name&status=Imported'

      $httpBackend.expectGET(url).respond('{"data_sets": [{"name": "Some name", "id": "'+ DS_ID + '"}]}')

      createController "DatasetSelectCtrl"
      $rootScope.init
        id: HANDLER_ID
        TYPE: 'json'
      $httpBackend.flush()

      expect($rootScope.datasets[0].id).toEqual('')
      expect($rootScope.datasets[1].id).toEqual(DS_ID)
      expect($rootScope.datasets[1].name).toEqual('Some name')

  # TODO: solve the "Unknown provider: dialogProvider" issue and test
  xdescribe "LoadDataDialogCtrl", ->

    it "should make no query", inject () ->
      createController "LoadDataDialogCtrl"
