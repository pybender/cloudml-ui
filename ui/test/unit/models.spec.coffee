'use strict'

# jasmine specs for models

describe "models", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.weights.model")

  beforeEach(module "app.models.controllers")
  beforeEach(module "app.models.model")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $dialog = null
  createController = null
  Model = null

  MODEL_ID = '556566767676767676'
  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $dialog = $injector.get('$dialog')
    Model = $injector.get('Model')

    BASE_URL = settings.apiUrl + 'models/'

    spyOn($location, 'path')

    createController = (ctrl) ->
      $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "ModelListCtrl", ->

    it "should make no query", inject () ->
      createController "ModelListCtrl"

  describe "TagCloudCtrl", ->

    it "should make tag list query", inject () ->
      url = settings.apiUrl + 'tags/?show=' + encodeURIComponent('text,count')
      $httpBackend.expectGET(url).respond('{"tags": [{"text": "smth"}]}')

      createController "TagCloudCtrl"
      $httpBackend.flush()

      expect($rootScope.tag_list[0].text).toBe('smth')

  describe "AddModelCtl", ->

    it "should init empty model", inject () ->
      createController "AddModelCtl"
      expect($rootScope.model).toBeDefined()

  describe "UploadModelCtl", ->

    it "should init empty model", inject () ->
      createController "UploadModelCtl"
      expect($rootScope.model).toBeDefined()

  describe "ModelDetailsCtrl", ->
    beforeEach ->
      url = settings.apiUrl + 'tags/?show=' + encodeURIComponent('text,id')
      $httpBackend.expectGET(url).respond('{"tags": [{"text": "smth"}]}')

      $routeParams.id = MODEL_ID
      $rootScope.initSections = jasmine.createSpy()

      createController "ModelDetailsCtrl"
      $httpBackend.flush()

      # TODO: more expectations

    it "should make details request", inject () ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + encodeURIComponent('created_on,target_variable,
error,labels,weights_synchronized,example_id,example_label,
updated_on,feature_count,test_import_handler.name,
train_import_handler.name,train_import_handler.import_params,tags,
test_import_handler.import_params,train_import_handler._id,
test_import_handler._id,memory_usage,created_by,trained_by,datasets,data_fields,
train_records_count,name,_id,status')
      $httpBackend.expectGET(url).respond('{"model": [{"_id": "' + MODEL_ID + '"}]}')

      $rootScope.goSection(['model'])
      $httpBackend.flush()

      # TODO: more expectations

    it "should request only features", inject () ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + encodeURIComponent('features,name,_id,status')
      $httpBackend.expectGET(url).respond('{"model": [{"_id": "' + MODEL_ID + '"}]}')

      $rootScope.goSection(['features'])
      $httpBackend.flush()

      # TODO: more expectations

    xit "should load tests", inject () ->
      url = BASE_URL + MODEL_ID + '/tests/?show=' + encodeURIComponent('name,
created_on,status,parameters,accuracy,examples_count,created_by')
      $httpBackend.expectGET(url).respond('{"tests": []}')

      $rootScope.LOADED_SECTIONS.push 'main'

      $rootScope.goSection(['test'])
      $httpBackend.flush()

      # TODO: more expectations

    # TODO: solve the issue with "TypeError: 'undefined' is not an object (evaluating 'fn.apply')"
    xit "should send tags update query", inject () ->
      url = BASE_URL + MODEL_ID + '/tests/?show=' + encodeURIComponent('name,
created_on,status,parameters,accuracy,examples_count,created_by')
      $httpBackend.expectPUT(url).respond('{"tests": []}')

      $rootScope.model = Model({
        _id: MODEL_ID,
        name: 'Model1',
        status: 'New',
        features: '',
        weights_synchronized: true
      })
      $rootScope.params = {
        'tags': ['tag1', 'tag2']
      }

      $rootScope.updateTags()
      $httpBackend.flush()

  describe "BaseModelDataSetActionCtrl", ->

    it "should init form", inject () ->
      $rootScope.handler = {
        import_params: {from: '', to: ''}
      }
      $rootScope.formElements = {}

      createController "BaseModelDataSetActionCtrl"

      expect($rootScope.select2Options).toBeDefined()
      expect(_.keys($rootScope.formElements).length).toBeGreaterThan(2)



































