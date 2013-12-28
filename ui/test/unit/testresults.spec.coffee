'use strict'

# jasmine specs for testresults

describe "testresults", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.models.model")
  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.features.models")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.datas.model")

  beforeEach(module "app.testresults.model")
  beforeEach(module "app.testresults.controllers")

  $rootScope = null
  createController = null
  settings = null
  $controller = null
  $httpBackend = null
  $routeParams = null

  BASE_URL = null

  beforeEach(inject(($injector) ->
    $rootScope = $injector.get('$rootScope')
    settings = $injector.get('settings')
    $controller = $injector.get('$controller')
    $httpBackend = $injector.get('$httpBackend')
    $routeParams = $injector.get('$routeParams')

    BASE_URL = settings.apiUrl + 'models/somemodelid/tests/sometestid/'

    createController = (ctrl) ->
      $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "TestListCtrl", ->

    it "should init controller, make no request", inject () ->
      createController "TestListCtrl"
      $rootScope.init({id: 'someid'})
      expect($rootScope.ACTION).toEqual('loading tests')
      expect($rootScope.FIELDS).toBeDefined()

  describe "TestDialogController", ->

    # TODO: find a way to inject dialog
    xit "should init controller, make no request", inject () ->
      createController "TestDialogController"

  describe "DeleteTestCtrl", ->

    # TODO: find a way to inject dialog
    xit "should init controller, make no request", inject () ->
      createController "DeleteTestCtrl"

  describe "TestDetailsCtrl", ->

    beforeEach ->
      $routeParams.model_id = 'somemodelid'
      $routeParams.id = 'sometestid'

      $rootScope.initSections = jasmine.createSpy()
      $rootScope.setSection = jasmine.createSpy()

      createController "TestDetailsCtrl"

    it "should load 'about' section", inject () ->
      url = BASE_URL + '?show=' + encodeURIComponent('classes_set,created_on,
parameters,error,examples_count,dataset,memory_usage,created_by,
examples_placement,examples_fields,examples_size,examples_placement,name,status,created_on,created_by')
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['about', 'details'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

    it "should load 'metrics' section", inject () ->
      url = BASE_URL + '?show=' + encodeURIComponent('accuracy,
metrics,examples_placement,name,status,created_on,created_by')
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['metrics', 'accuracy'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

    it "should load 'matrix' section", inject () ->
      url = BASE_URL + '?show=' + encodeURIComponent('metrics,
confusion_matrix_calculations,model,examples_placement,name,status,created_on,created_by')
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['matrix', 'confusion'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

  describe "TestActionsCtrl", ->

    it "should init controller, make no request", inject () ->
      createController "TestActionsCtrl"
      $rootScope.init({model: {}, test: {id: 'sometestid'}})

      expect($rootScope.test.id).toEqual('sometestid')

    it "should open delete dialog", inject () ->
      url = 'partials/testresults/delete_popup.html'
      $httpBackend.expectGET(url).respond('')

      $rootScope.test = {
        id: 'sometestid',
        model: {id: 'somemodelid'}
      }
      $rootScope.resetError = jasmine.createSpy()

      createController "TestActionsCtrl"
      $rootScope.delete_test()
      $httpBackend.flush()

      expect($rootScope.resetError).toHaveBeenCalled()

  describe "TestExportsCtrl", ->

    it "should init controller, request current exports", inject (TestResult) ->
      url = BASE_URL + 'action/exports/?'
      $httpBackend.expectGET(url).respond('{"exports": [{"status": "In Progress"}, {"status": "Completed"}],
 "test": {"dataset": {}}}')

      test = new TestResult({id: 'sometestid', model_id: 'somemodelid'})

      jasmine.Clock.useMock()

      createController "TestExportsCtrl"
      $rootScope.init(test)
      $httpBackend.flush()

      expect($rootScope.exports[0].status).toEqual('In Progress')
      expect($rootScope.exports[1].status).toEqual('Completed')

      $httpBackend.expectGET(url).respond('{"exports": [{"status": "Completed"}, {"status": "Completed"}],
 "test": {"dataset": {}}}')

      jasmine.Clock.tick(1001)
      $httpBackend.flush()

      expect($rootScope.exports[0].status).toEqual('Completed')
      expect($rootScope.exports[1].status).toEqual('Completed')

  describe "TestConfusionMatrixCtrl", ->

    beforeEach inject (TestResult) ->
      createController "TestConfusionMatrixCtrl"

      # Metrics are supposed to be filled
      $rootScope.test = new TestResult({
        id: 'sometestid',
        model_id: 'somemodelid'},
        metrics: {}
      )

#     it "should request confusion matrix", inject () ->
#       url = BASE_URL + 'action/confusion_matrix/?weight0=42&weight1=38'
#       $httpBackend.expectGET(url).respond('{"confusion_matrix": [1,2,3,4],
# "test": {}}')

#       $rootScope.recalculate(42, 38)
#       $httpBackend.flush()

    it "should reload items", inject () ->
      url = BASE_URL + '?show=' + encodeURIComponent('confusion_matrix_calculations')
      $httpBackend.expectGET(url).respond('{"test": {"confusion_matrix_calculations": [
{"status": "Completed", "weights": [42, 38]}]}}')

      $rootScope.reload()
      $httpBackend.flush()
