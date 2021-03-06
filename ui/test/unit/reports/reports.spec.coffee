'use strict'

# jasmine specs for reports

describe "reports", ->

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
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.datas.model")
  beforeEach(module "app.features.models")

  beforeEach(module "app.reports.model")
  beforeEach(module "app.reports.controllers")

  $rootScope = null
  createController = null
  settings = null
  $controller = null
  $httpBackend = null

  beforeEach(inject(($injector) ->
    $rootScope = $injector.get('$rootScope')
    settings = $injector.get('settings')
    $controller = $injector.get('$controller')
    $httpBackend = $injector.get('$httpBackend')

    createController = (ctrl) ->
      $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "CompareModelsFormCtl", ->

    it "should init controller", inject ($routeParams) ->
      $routeParams.action = 'some_action:second_part'

      createController "CompareModelsFormCtl"
      expect($rootScope.action).toEqual(['some_action', 'second_part'])

    it "should init form", inject ($routeParams) ->
      url = settings.apiUrl + 'models/?comparable=1&show=name'
      $httpBackend.expectGET(url).respond('{"models": []}')

      createController "CompareModelsFormCtl"
      $rootScope.initForm()
      $httpBackend.flush()

    it "should init model", inject () ->
      url = settings.apiUrl + 'models/modelid123/tests/?model_id=modelid123&status=Completed'
      $httpBackend.expectGET(url).respond('{"tests": []}')

      item = {
        model: {'id': 'modelid123'}
      }

      createController "CompareModelsFormCtl"
      $rootScope.changeModel(item)
      $httpBackend.flush()

    it "should generate report", inject (CompareReport) ->
      url = settings.apiUrl + 'reports/compare/?model1=model1id&model2=model2id&test1=test1id&test2=test2id'
      $httpBackend.expectGET(url).respond('{"data": []}')

      data = [
        {
          model: {id: 'model1id'},
          test: {id: 'test1id'},
        },
        {
          model: {id: 'model2id'},
          test: {id: 'test2id'},
        }
      ]
      $rootScope.report = new CompareReport(data)

      createController "CompareModelsFormCtl"
      $rootScope.generate()

      $httpBackend.flush()
