'use strict'

# jasmine specs for testresults

describe "testresults", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.models.model")
  beforeEach(module "app.importhandlers.models")
  beforeEach(module "app.importhandlers.xml.models")
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

    BASE_URL = settings.apiUrl + 'models/1234/tests/4321/'

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
      $rootScope.init({id: '123'})
      expect($rootScope.ACTION).toEqual('loading tests')
      expect($rootScope.FIELDS).toBeDefined()

  describe "TestDetailsCtrl", ->

    beforeEach ->
      $routeParams.model_id = '1234'
      $routeParams.id = '4321'

      $rootScope.initSections = jasmine.createSpy()
      $rootScope.setSection = jasmine.createSpy()

      createController "TestDetailsCtrl"

    it "should load 'about' section", inject (TestResult) ->
      url = BASE_URL + '?show=' + TestResult.EXTRA_FIELDS + ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['about', 'details'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

    it "should load 'metrics' section", inject (TestResult) ->
      url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' + ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['metrics', 'accuracy'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

    it "should load 'metrics' section, old list format, binary classifier before 20140710",
      inject (TestResult) ->
        url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' +
          ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
        $httpBackend.expectGET(url)
        .respond.apply @, map_url_to_response(url,
          'binary classification arrays format before 20140710')

        $rootScope.goSection(['metrics', 'accuracy'])
        $httpBackend.flush()

        expect($rootScope.rocCurves).toBeDefined()
        expect(_.keys($rootScope.rocCurves).length).toEqual 1
        expect($rootScope.rocCurves[1]).toBeDefined()
        expect($rootScope.rocCurves[1]['curve']).toBeDefined()
        expect($rootScope.rocCurves[1]['roc_auc']).toBeDefined()
        expect($rootScope.prCurves).toBeDefined()
        expect($rootScope.prCurves['Precision-Recall curve']).toBeDefined()

    it "should load 'metrics' section for multiclass classifier format after 20140710",
      inject (TestResult) ->
        url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' +
          ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
        $httpBackend.expectGET(url)
        .respond.apply @, map_url_to_response(url,
            'multiclass classification model dict format after 20140710')

        $rootScope.goSection(['metrics', 'accuracy'])
        $httpBackend.flush()


        expect($rootScope.rocCurves).toBeDefined()
        expect(_.keys($rootScope.rocCurves).length).toEqual 3
        for key in _.keys($rootScope.rocCurves)
          expect($rootScope.rocCurves[key]['curve']).toBeDefined()
          expect($rootScope.rocCurves[key]['roc_auc']).toBeDefined()

        expect($rootScope.prCurves).toBeUndefined() # multiclass has no pr

    it "should load 'metrics' section for multiclass classifier format after 20140907",
      inject (TestResult) ->
        url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' +
          ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
        $httpBackend.expectGET(url)
        .respond.apply @, map_url_to_response(url,
          'multiclass classification model dict format after 20140710')

        $rootScope.goSection(['metrics', 'accuracy'])
        $httpBackend.flush()


        expect($rootScope.rocCurves).toBeDefined()
        expect(_.keys($rootScope.rocCurves).length).toEqual 3
        for key in _.keys($rootScope.rocCurves)
          expect($rootScope.rocCurves[key]['curve']).toBeDefined()
          expect($rootScope.rocCurves[key]['roc_auc']).toBeDefined()

        expect($rootScope.prCurves).toBeUndefined() # multiclass has no pr

    it "should load 'metrics' section for binary classifier, format after 20140710",
      inject (TestResult) ->
        url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' +
          ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
        $httpBackend.expectGET(url)
        .respond.apply @, map_url_to_response(url,
          'binary classification model dict format after 20140710')

        $rootScope.goSection(['metrics', 'accuracy'])
        $httpBackend.flush()

        expect($rootScope.prCurves).toBeDefined() # binary classification has pr

        expect($rootScope.rocCurves).toBeDefined()
        expect(_.keys($rootScope.rocCurves).length).toEqual 1
        expect($rootScope.rocCurves[1]).toBeDefined()
        expect($rootScope.rocCurves[1]['curve']).toBeDefined()
        expect($rootScope.rocCurves[1]['roc_auc']).toBeDefined()
        expect($rootScope.prCurves).toBeDefined()
        expect($rootScope.prCurves['Precision-Recall curve']).toBeDefined()

    it "should load 'metrics' section for binary classifier, format after 20140907",
      inject (TestResult) ->
        url = BASE_URL + '?show=' + 'accuracy,metrics,roc_auc' +
          ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
        $httpBackend.expectGET(url)
        .respond.apply @, map_url_to_response(url,
          'binary classification model dict format after 20140907')

        $rootScope.goSection(['metrics', 'accuracy'])
        $httpBackend.flush()

        expect($rootScope.prCurves).toBeDefined() # binary classification has pr

        expect($rootScope.rocCurves).toBeDefined()
        expect(_.keys($rootScope.rocCurves).length).toEqual 1
        expect($rootScope.rocCurves[1]).toBeDefined()
        expect($rootScope.rocCurves[1]['curve']).toBeDefined()
        expect($rootScope.rocCurves[1]['roc_auc']).toBeDefined()
        expect($rootScope.prCurves).toBeDefined()
        expect($rootScope.prCurves['Precision-Recall curve']).toBeDefined()

    it "should load 'matrix' section", inject (TestResult) ->
      url = BASE_URL + '?show=' + TestResult.MATRIX_FIELDS + ',examples_placement,fill_weights,' + TestResult.MAIN_FIELDS
      $httpBackend.expectGET(url).respond('{"test": {}}')

      $rootScope.goSection(['matrix', 'confusion'])
      $httpBackend.flush()

      expect($rootScope.setSection).toHaveBeenCalled()

  describe "TestActionsCtrl", ->

    it "should init controller, make no request", inject () ->
      createController "TestActionsCtrl"
      $rootScope.init({model: {}, test: {id: '1234'}})

      expect($rootScope.test.id).toEqual('1234')

    it "should open delete dialog", ->

      $rootScope.test = {
        id: '4321',
        model: {id: '1234', objectUrl: -> 'zinger'}
      }
      $rootScope.resetError = jasmine.createSpy('$scope.resetError')
      $rootScope.openDialog = jasmine.createSpy('$scope.openDialog')

      createController "TestActionsCtrl"
      $rootScope.delete_test()

      expect($rootScope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: $rootScope.test
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete Test'
        path: $rootScope.test.model.objectUrl()
      expect($rootScope.openDialog.calls.mostRecent().args[0]).toEqual $rootScope

  describe "TestExportsCtrl", ->

    it "should init controller, request current exports", inject (TestResult, $timeout) ->
      url = BASE_URL + 'action/exports/'
      response =
        exports: [{status: 'In Progress'}, {status: 'Completed'}]
        db_exports: [{status: 'Nothing'}, {status: 'In Progress'}]
        test: {dataset: {}}
      $httpBackend.expectGET(url).respond 200, angular.toJson response

      test = new TestResult({id: '4321', model_id: '1234'})

      createController "TestExportsCtrl"
      $rootScope.init(test)
      $httpBackend.flush()

      expect($rootScope.exports[0].status).toEqual('In Progress')
      expect($rootScope.exports[1].status).toEqual('Completed')
      expect($rootScope.db_exports[0].status).toEqual('Nothing')
      expect($rootScope.db_exports[1].status).toEqual('In Progress')
      expect($rootScope.test).toEqual test

      response =
        exports: [{status: 'Completed'}, {status: 'Completed'}]
        db_exports: [{status: 'Nothing'}, {status: 'Completed'}]
        test: {dataset: {}}
      $httpBackend.expectGET(url).respond 200, angular.toJson response

      $timeout.flush()
      $httpBackend.flush()

      expect($rootScope.exports[0].status).toEqual('Completed')
      expect($rootScope.exports[1].status).toEqual('Completed')
      expect($rootScope.db_exports[0].status).toEqual('Nothing')
      expect($rootScope.db_exports[1].status).toEqual('Completed')
      expect($rootScope.test).toEqual test

  describe "TestConfusionMatrixCtrl", ->

    beforeEach inject (TestResult) ->
      createController "TestConfusionMatrixCtrl"

      # Metrics are supposed to be filled
      $rootScope.test = new TestResult({
        id: '4321',
        model_id: '1234'},
        metrics: {}
      )

#     it "should request confusion matrix", inject () ->
#       url = BASE_URL + 'action/confusion_matrix/?weight0=42&weight1=38'
#       $httpBackend.expectGET(url).respond('{"confusion_matrix": [1,2,3,4],
# "test": {}}')

#       $rootScope.recalculate(42, 38)
#       $httpBackend.flush()

    it "should reload items", inject () ->
      url = BASE_URL + '?show=' + 'confusion_matrix_calculations'
      $httpBackend.expectGET(url).respond('{"test": {"confusion_matrix_calculations": [
{"status": "Completed", "weights": [42, 38]}]}}')

      $rootScope.reload()
      $httpBackend.flush()
