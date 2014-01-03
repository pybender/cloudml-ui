'use strict'

# jasmine specs for test examples

describe "test examples", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.models.model")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.features.models")

  beforeEach(module "app.datas.model")
  beforeEach(module "app.datas.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $dialog = null
  createController = null

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
    $dialog = $injector.get('$dialog')

    spyOn($location, 'path')
    spyOn($location, 'search')

    BASE_URL = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/examples/'

    createController = (ctrl) ->
       $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "TestExamplesCtrl", ->

    it "should make no query", inject () ->
      createController "TestExamplesCtrl"

    it "should make initialization requests", inject (TestResult) ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + encodeURIComponent('name,examples_fields')
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      # TODO: Can we get rid of this request?
      url = settings.apiUrl + 'models/' + MODEL_ID + '/?show=' + encodeURIComponent('name,labels')
      $httpBackend.expectGET(url).respond('{"model": {"labels": ["0", "1"]}}')

      test = new TestResult({
        id: TEST_ID,
        model_id: MODEL_ID
      })

      createController "TestExamplesCtrl"
      $rootScope.init(test)
      $httpBackend.flush()

      expect($rootScope.test).toEqual(test)
      expect($rootScope.labels).toEqual(['0', '1'])

    it "should make initialization requests using filters", inject (TestResult) ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + encodeURIComponent('name,examples_fields')
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      # TODO: Can we get rid of this request?
      url = settings.apiUrl + 'models/' + MODEL_ID + '/?show=' + encodeURIComponent('name,labels')
      $httpBackend.expectGET(url).respond('{"model": {"labels": ["0", "1"]}}')

      test = new TestResult({
        id: TEST_ID,
        model_id: MODEL_ID,
        examples_fields: ['some_field', 'data_field']
      })

      createController "TestExamplesCtrl"

      $rootScope.filter_opts = {
        label: '0',
        some_field: 'val1',
        'data_field': 'val2',
      }

      $rootScope.init(test)
      $httpBackend.flush()

      expect($rootScope.test).toEqual(test)
      expect($rootScope.labels).toEqual(['0', '1'])
      expect($location.search).toHaveBeenCalledWith({
        'label': '0',
        'some_field': 'val1',
        'data_field': 'val2',
        action: 'examples:list',
      })

    xit "should make list query", inject () ->
      fields = "id,name,label,pred_label,title,probs"
      url = BASE_URL + '?show=' + encodeURIComponent(fields)
      $httpBackend.expectGET(url).respond('{"datas": [{"id": "123"}]}')

      $rootScope.test = {
        id: TEST_ID,
        model_id: MODEL_ID
      }

      createController "TestExamplesCtrl"
      $rootScope.loadDatas()({filter_opts: {}})
      expect($rootScope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($rootScope.loading_state).toBeFalsy()

    it "should make filter params", inject () ->
      createController "TestExamplesCtrl"
      $rootScope.simple_filters = {'label': '1'}
      $rootScope.data_filters = [{name: 'field', value: 'val'}]
      $rootScope.filter()

      expect($location.search).toHaveBeenCalledWith({
        'label': '1',
        'field': 'val'
      })

  describe "GroupedExamplesCtrl", ->

    it "should make requests", inject () ->
      url = settings.apiUrl + 'models/' + MODEL_ID + '/tests/' + TEST_ID + '/?show=' + encodeURIComponent('name,examples_fields')
      $httpBackend.expectGET(url).respond('{"test": {"name": "Some"}}')

      $routeParams.model_id = MODEL_ID
      $routeParams.test_id = TEST_ID

      createController "GroupedExamplesCtrl"
      expect($rootScope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($rootScope.loading_state).toBeFalsy()
      expect($rootScope.test.id).toEqual(TEST_ID)

      url = BASE_URL + 'action/groupped/?count=2&field=application_id'
      $httpBackend.expectGET(url).respond('{"test_examples": []}')

      $rootScope.form = {
        'field': 'application_id',
        'count': 2
      }

      $rootScope.update()
      expect($rootScope.loading_state).toBeTruthy()

      $httpBackend.flush()

      expect($rootScope.loading_state).toBeFalsy()

  describe "ExampleDetailsCtrl", ->

    it "should make details request", inject () ->
      fields = 'test_name,weighted_data_input,model,pred_label,
label,prob,created_on,test_result'
      url = BASE_URL + EXAMPLE_ID + '/?show=' + encodeURIComponent(fields)
      $httpBackend.expectGET(url).respond('{"data": {"id": "' + EXAMPLE_ID + '"}}')

      $routeParams.model_id = MODEL_ID
      $routeParams.test_id = TEST_ID
      $routeParams.id = EXAMPLE_ID

      createController "ExampleDetailsCtrl"
      $httpBackend.flush()

      expect($rootScope.data.id).toEqual(EXAMPLE_ID)

  describe "CsvDownloadCtrl", ->

    # TODO: find a way to inject dialog
    xit "should load data fields", inject () ->  # disabled
      url = BASE_URL + 'action/datafields/?'
      $httpBackend.expectGET(url).respond('{"fields": ["one", "two"]}')

      test = {
        id: TEST_ID,
        model_id: MODEL_ID
      }

      createController "CsvDownloadCtrl"
      $httpBackend.flush()

      expect($rootScope.selectFields).toEqual(['data_input.one', 'data_input.two'])
      expect($rootScope.loading_state).toBeFalsy()
