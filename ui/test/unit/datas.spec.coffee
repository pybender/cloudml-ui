'use strict'

# jasmine specs for test examples

describe "test examples", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.models.model")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.xml_importhandlers.models")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.features.models")

  beforeEach(module "app.datas.model")
  beforeEach(module "app.datas.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $modal = null
  createController = null
  $scope = null

  MODEL_ID = '52231c7c07dbec2d26c73315'
  TEST_ID = '522456a107dbec1e3dd700b7'
  EXAMPLE_ID = '52222222222222222222222'

  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $modal = $injector.get('$modal')

    spyOn($location, 'path')
    spyOn($location, 'search')

    BASE_URL = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/examples/'

    $rootScope.setError = jasmine.createSpy '$rootScope.setErr'

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

  describe "TestExamplesCtrl", ->

    it "should make no query", inject () ->
      createController "TestExamplesCtrl"

    it "should make initialization requests", inject (TestResult) ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + 'name,examples_fields'
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      # TODO: Can we get rid of this request?
      url = settings.apiUrl + 'models/' + MODEL_ID + '/?show=' + 'name,labels'
      $httpBackend.expectGET(url).respond('{"model": {"labels": ["0", "1"]}}')

      test = new TestResult({
        id: TEST_ID,
        model_id: MODEL_ID
      })

      createController "TestExamplesCtrl"
      $scope.init(test)
      $httpBackend.flush()

      expect($scope.test).toEqual(test)
      expect($scope.labels).toEqual(['0', '1'])

    it "should make initialization requests using filters", inject (TestResult) ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + 'name,examples_fields'
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      # TODO: Can we get rid of this request?
      url = settings.apiUrl + 'models/' + MODEL_ID + '/?show=' + 'name,labels'
      $httpBackend.expectGET(url).respond('{"model": {"labels": ["0", "1"]}}')

      test = new TestResult({
        id: TEST_ID,
        model_id: MODEL_ID,
        examples_fields: ['some_field', 'data_field']
      })

      createController "TestExamplesCtrl"

      $scope.filter_opts = {
        label: '0',
        some_field: 'val1',
        'data_field': 'val2',
      }

      $scope.init(test)
      $httpBackend.flush()

      expect($scope.test).toEqual(test)
      expect($scope.labels).toEqual(['0', '1'])
      expect($location.search).toHaveBeenCalledWith
        sort_by: ''
        order: 'asc'
        label: '0'
        some_field: 'val1'
        data_field: 'val2'

    it "should make list query", inject (Data) ->
      d = new Data {id: 123, model_id: MODEL_ID, test_id: TEST_ID}
      response = {}
      response[d.API_FIELDNAME + 's'] = [d]
      $httpBackend.expectGET "#{d.BASE_API_URL}?order=asc&show=id,name,label,pred_label,title,prob,example_id&sort_by="
      .respond 200, angular.toJson response

      createController "TestExamplesCtrl"
      $scope.test = {
        id: TEST_ID,
        model_id: MODEL_ID
      }
      $scope.loadDatas()({filter_opts: {}})
      expect($scope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($scope.loading_state).toBeFalsy()

    it "should make filter params", inject () ->
      createController "TestExamplesCtrl"
      $scope.simple_filters = {'label': '1'}
      $scope.data_filters = [{name: 'field', value: 'val'}]
      $scope.filter()

      expect($location.search).toHaveBeenCalledWith
        sort_by: ''
        order: 'asc'
        label: '1'
        field: 'val'

  describe "GroupedExamplesCtrl", ->

    it "should make requests", inject () ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + 'name,examples_fields'
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      $routeParams.model_id = MODEL_ID
      $routeParams.test_id = TEST_ID

      createController "GroupedExamplesCtrl"
      expect($scope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($scope.loading_state).toBeFalsy()
      expect($scope.test.id).toEqual(TEST_ID)

      url = BASE_URL + 'action/groupped/?count=2&field=application_id'
      $httpBackend.expectGET(url).respond('{"test_examples": []}')

      $scope.form = {
        'field': 'application_id',
        'count': 2
      }

      $scope.update()
      expect($scope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($scope.loading_state).toBeFalsy()

  describe "ExampleDetailsCtrl", ->

    it "should make details request", inject () ->
      fields = ['test_name','weighted_data_input','model', 'pred_label',
                'label','prob','created_on','test_result', 'next', 'previous',
                'parameters_weights', 'data_input'].join(',')
      url = BASE_URL + EXAMPLE_ID + '/?show=' + fields
      $httpBackend.expectGET(url).respond('{"data": {"id": "' + EXAMPLE_ID + '"}}')

      $routeParams.model_id = MODEL_ID
      $routeParams.test_id = TEST_ID
      $routeParams.id = EXAMPLE_ID

      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      createController "ExampleDetailsCtrl"
      expect($rootScope.initSections).toHaveBeenCalledWith $scope.goSection
      $scope.goSection()
      $httpBackend.flush()

      expect($scope.data.id).toEqual(EXAMPLE_ID)

  xdescribe "CsvDownloadCtrl", ->

    it "should load data fields",
      inject (TestResult) ->
        url = BASE_URL + 'action/datafields/'
        $httpBackend.expectGET(url).respond('{"fields": ["2two", "1one", "4four", "3three"]}')

        openOptions =
          model: new TestResult {id: TEST_ID, model_id: MODEL_ID}

        createController "CsvDownloadCtrl", {'openOptions': openOptions}
        $httpBackend.flush()

        # retrieve fields without reordering
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '1one', '4four', '3three'])
        expect($rootScope.selectFields).toEqual []
        expect($rootScope.loading_state).toBeFalsy()

        # removing a field
        $rootScope.removeField '4four'
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '1one', '3three'])
        expect($rootScope.selectFields).toEqual ['4four']

        # removing a field (again just to make sure)
        $rootScope.removeField '4four'
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '1one', '3three'])
        expect($rootScope.selectFields).toEqual ['4four']

        # removing another field, should reorder selectFields
        $rootScope.removeField '1one'
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '3three'])
        expect($rootScope.selectFields).toEqual ['1one', '4four']

        # append a field
        $rootScope.csvField = '1one'
        $rootScope.appendField()
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '3three', '1one'])
        expect($rootScope.selectFields).toEqual ['4four']

        # append the same field again
        $rootScope.csvField = '1one'
        $rootScope.appendField()
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '3three', '1one'])
        expect($rootScope.selectFields).toEqual ['4four']

        # append a bogus
        $rootScope.csvField = 'bogus'
        $rootScope.appendField()
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['2two', '3three', '1one'])
        expect($rootScope.selectFields).toEqual ['4four']

        # remove all
        $rootScope.removeAll()
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual([])
        expect($rootScope.selectFields).toEqual ['1one', '2two', '3three', '4four']

        # add all
        $rootScope.addAll()
        expect($rootScope.stdFields).toEqual(['name', 'id', 'label', 'pred_label', 'prob'])
        expect($rootScope.extraFields).toEqual(['1one', '2two', '3three', '4four'])
        expect($rootScope.selectFields).toEqual []

        # get csv
        $rootScope.$broadcast = jasmine.createSpy('$scope.$broadcast')
        $rootScope.close = jasmine.createSpy('$scope.close')
        $location.search = jasmine.createSpy('$location.search')
        url = BASE_URL + "action/csv/?show=#{$rootScope.stdFields.join(',')},#{$rootScope.extraFields.join(',')}"
        $httpBackend.expectGET(url).respond("{\"url\":\"#{url}\"}")

        $rootScope.getExamplesCsv()
        $httpBackend.flush()
        expect($rootScope.loading_state).toBe false
        expect($location.search).toHaveBeenCalledWith 'action=about:details'
        expect($rootScope.close).toHaveBeenCalled()
        expect($rootScope.$broadcast).toHaveBeenCalledWith 'exportsChanged'
        expect(appendSpy).toHaveBeenCalledWith 'fields', angular.toJson($rootScope.stdFields.concat($rootScope.extraFields))

        # get csv, something went bad
        $rootScope.setError = jasmine.createSpy('$scope.setError')
        $rootScope.close = jasmine.createSpy('$scope.close')
        $location.search = jasmine.createSpy('$location.search')
        url = BASE_URL + "action/csv/?show=#{$rootScope.stdFields.join(',')},#{$rootScope.extraFields.join(',')}"
        $httpBackend.expectGET(url).respond(400)

        $rootScope.getExamplesCsv()
        $httpBackend.flush()
        expect($rootScope.loading_state).toBe false
        expect($rootScope.setError).toHaveBeenCalled()
