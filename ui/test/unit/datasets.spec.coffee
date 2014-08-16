'use strict'

# jasmine specs for datasets

describe "datasets", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
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
  $modal = null
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
    $modal = $injector.get('$modal')

    spyOn($window.location, 'replace')

    BASE_URL = settings.apiUrl + 'importhandlers/json/' + HANDLER_ID + '/datasets/'

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $rootScope }
      $controller(ctrl, injected)
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

      url = BASE_URL + DS_ID + '/action/generate_url/'
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

      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      url2 = BASE_URL + DS_ID + '/action/sample_data/?size=5'
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

    it "should handle load errors", inject (DataSet)->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'
      $rootScope.initSections = jasmine.createSpy()

      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      $httpBackend.expectGET(url1).respond(400)

      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      createController "DataSetDetailsCtrl"

      $rootScope.go()
      $httpBackend.flush()

      expect($rootScope.setError.callCount).toBe 1
      expect($rootScope.dataset.samples_json).toBe null

    it "should handle get sample error", inject (DataSet)->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'
      $rootScope.initSections = jasmine.createSpy()

      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      url2 = BASE_URL + DS_ID + '/action/sample_data/?size=5'
      $httpBackend.expectGET(url1).respond angular.toJson
        data_set:
          name: "Some name"
          status: "Imported"
      $httpBackend.expectGET(url2).respond(400)

      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      createController "DataSetDetailsCtrl"

      $rootScope.go()
      $httpBackend.flush()

      expect($rootScope.setError.callCount).toBe 1
      expect($rootScope.dataset.samples_json).toBe null

    it "should not request sample if dataset status is importing", inject (DataSet)->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'
      $rootScope.initSections = jasmine.createSpy()

      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      $httpBackend.expectGET(url1).respond angular.toJson
        data_set:
          name: "Some name"
          status: DataSet.STATUS_IMPORTING

      createController "DataSetDetailsCtrl"

      $rootScope.go()
      $httpBackend.flush()

      expect($rootScope.dataset.samples_json).toBe null

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

  describe "LoadDataDialogCtrl", ->

    it "should POST save and redirect", inject(
      ($location, DataSet) ->
        handlerType = 'xml'
        dialog =
          model:
            id: HANDLER_ID
            TYPE: handlerType
            import_params: ['start', 'end']
          close: jasmine.createSpy('dialog.close')

        $rootScope.close =
        $location.url = jasmine.createSpy('$location.url')
        url = "#{settings.apiUrl}importhandlers/#{handlerType}/#{HANDLER_ID}/datasets/"
        $httpBackend.expectPOST(url).respond angular.toJson
          data_set:
            id: DS_ID
            name: "dataset name"

        createController "LoadDataDialogCtrl",
          $location: $location
          dialog: dialog
          DataSet: DataSet

        $rootScope.start()
        $httpBackend.flush()

        expect(dialog.close).toHaveBeenCalled()
        expect($location.url).toHaveBeenCalledWith("/handlers/xml/#{HANDLER_ID}/datasets/#{DS_ID}")
    )

  describe "DataSet", ->

    it "should reimport", inject(
      (DataSet)->

        handlerType = 'xml'
        url = "#{settings.apiUrl}importhandlers/#{handlerType}/#{HANDLER_ID}/datasets/#{DS_ID}/action/reimport/"
        $httpBackend.expectPUT(url).respond angular.toJson
          data_set:
            uid: "d8e99ac218fa11e4aa9a000c29e3f35c"
            records_count: null
            id: DS_ID
            status: DataSet.STATUS_IMPORTING

        ds = new DataSet
          id: DS_ID
          import_handler_id: HANDLER_ID
          import_handler_type: 'xml'
          status: 'nothing'
        ds.$reimport()
        $httpBackend.flush()
        expect(ds.status).toEqual DataSet.STATUS_IMPORTING

        # should refuse to import
        ds = new DataSet
          id: DS_ID
          import_handler_id: HANDLER_ID
          import_handler_type: 'xml'
          status: DataSet.STATUS_IMPORTING
        expect(ds.$reimport).toThrow Error "Can't re-import a dataset that is importing now"
    )