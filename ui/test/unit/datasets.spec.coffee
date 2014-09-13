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
  $scope = null
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

    BASE_URL = settings.apiUrl + 'importhandlers/json/' + HANDLER_ID + '/datasets/'

    createController = (ctrl, extras) ->
      $scope = $rootScope.$new()
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
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

      $rootScope.openDialog = jasmine.createSpy('$rootScope.openDialog')

      createController "DatasetActionsCtrl"
      $scope.handler = new ImportHandler()
      $scope.handler.id = HANDLER_ID
      $scope.ds = new DataSet()
      $scope.delete()

      expect($scope.openDialog).toHaveBeenCalledWith
        model: $scope.ds
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete DataSet'
        path: $scope.handler.objectUrl()
        ownerScope: $scope

    it "should generate download link", inject (ImportHandler, DataSet) ->

      $window =
        location:
          replace: jasmine.createSpy '$window.location.replace'
      createController "DatasetActionsCtrl", {$window: $window}
      $scope.handler = new ImportHandler({id: HANDLER_ID})
      $scope.ds = new DataSet(
        {id: DS_ID, on_s3: true, import_handler_id: HANDLER_ID}
      )

      url = BASE_URL + DS_ID + '/action/generate_url/'
      $httpBackend.expectGET(url).respond('{"url": "http://amazon/ds_path"}')

      $scope.download()
      $httpBackend.flush()

      expect($window.location.replace).toHaveBeenCalledWith('http://amazon/ds_path')

  describe "DataSetDetailsCtrl", ->

    beforeEach ->
      $routeParams.import_handler_id = HANDLER_ID
      $routeParams.id = DS_ID
      $routeParams.import_handler_type = 'json'
      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it "should init sections", inject () ->
      createController "DataSetDetailsCtrl"
      expect($scope.initSections).toHaveBeenCalledWith(
        $scope.go, "model:details", simple=true
      )

    it "should make details query", inject (DataSet) ->
      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      url2 = BASE_URL + DS_ID + '/action/sample_data/?size=5'
      $httpBackend.expectGET(url1).respond('{"data_set": {"name": "Some name"}}')
      $httpBackend.expectGET(url2).respond('[{"contractor.dev_skill_test_passed_count": "18", "contractor.dev_bill_rate": "5.56"}]')

      createController "DataSetDetailsCtrl"
      expect($scope.initSections).toHaveBeenCalledWith(
        $scope.go, "model:details", simple=true
      )

      $scope.go()
      $httpBackend.flush()

      expect($scope.dataset).toBeDefined()
      expect($scope.dataset.name).toBe('Some name')
      expect($scope.dataset.samples_json).toEqual angular.toJson([
        'contractor.dev_skill_test_passed_count': '18'
        'contractor.dev_bill_rate': '5.56'
      ], true)

    it "should handle load errors", inject (DataSet)->
      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      $httpBackend.expectGET(url1).respond(400)

      createController "DataSetDetailsCtrl"

      $scope.go()
      $httpBackend.flush()

      expect($scope.setError.calls.count()).toBe 1
      expect($scope.dataset.samples_json).toBe null

    it "should handle get sample error", inject (DataSet)->
      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      url2 = BASE_URL + DS_ID + '/action/sample_data/?size=5'
      $httpBackend.expectGET(url1).respond angular.toJson
        data_set:
          name: "Some name"
          status: "Imported"
      $httpBackend.expectGET(url2).respond(400)

      createController "DataSetDetailsCtrl"

      $scope.go()
      $httpBackend.flush()

      expect($scope.setError.calls.count()).toBe 1
      expect($scope.dataset.samples_json).toBe null

    it "should not request sample if dataset status is importing", inject (DataSet)->
      url1 = BASE_URL + DS_ID + '/?show=' + DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      $httpBackend.expectGET(url1).respond angular.toJson
        data_set:
          name: "Some name"
          status: DataSet.STATUS_IMPORTING

      createController "DataSetDetailsCtrl"

      $scope.go()
      $httpBackend.flush()

      expect($scope.dataset.samples_json).toBe null

  describe "DatasetSelectCtrl", ->

    it "should make list query", inject () ->
      url = settings.apiUrl + 'importhandlers/json/' + HANDLER_ID +
        '/datasets/?import_handler_id=522333333344445d26c73315&import_handler_type=json&show=name&status=Imported'

      $httpBackend.expectGET(url).respond('{"data_sets": [{"name": "Some name", "id": "'+ DS_ID + '"}]}')

      createController "DatasetSelectCtrl"
      $scope.init
        id: HANDLER_ID
        TYPE: 'json'
      $httpBackend.flush()

      expect($scope.datasets[0].id).toEqual('')
      expect($scope.datasets[1].id).toEqual(DS_ID)
      expect($scope.datasets[1].name).toEqual('Some name')

  describe "LoadDataDialogCtrl", ->

    it "should POST save and redirect", inject(
      ($location, DataSet) ->
        handlerType = 'xml'
        openOptions =
          model:
            id: HANDLER_ID
            TYPE: handlerType
            import_params: ['start', 'end']

        $rootScope.$close = jasmine.createSpy('$rootScope.$close')
        $location.url = jasmine.createSpy('$location.url')
        url = "#{settings.apiUrl}importhandlers/#{handlerType}/#{HANDLER_ID}/datasets/"
        $httpBackend.expectPOST(url).respond angular.toJson
          data_set:
            id: DS_ID
            name: "dataset name"

        createController "LoadDataDialogCtrl",
          $location: $location
          openOptions: openOptions
          DataSet: DataSet

        $scope.start()
        $httpBackend.flush()

        expect($scope.$close).toHaveBeenCalled()
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