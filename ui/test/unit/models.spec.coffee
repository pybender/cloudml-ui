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
  beforeEach(module "app.xml_importhandlers.models")
  beforeEach(module "app.datasets.model")
  beforeEach(module "app.testresults.model")
  beforeEach(module "app.weights.model")
  beforeEach(module "app.features.models")

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

      expect($rootScope.model.id).toEqual(MODEL_ID)
      expect($rootScope.LOADED_SECTIONS).toBeDefined()
      expect($rootScope.select2params).toBeDefined()
      expect($rootScope.params).toBeDefined()
      expect($rootScope.tag_list).toBeDefined()
      expect($rootScope.tag_list[0].text).toEqual('smth')

    it "should make details request", inject () ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + encodeURIComponent(MODEL_FIELDS + ',' + FIELDS_BY_SECTION['model'])
      $httpBackend.expectGET(url)
      .respond.apply @, map_url_to_response(url,
        'multiclass model main fields')

      $rootScope.goSection(['model'])
      $httpBackend.flush()

    it "should request only features", inject () ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + encodeURIComponent(FIELDS_BY_SECTION['main'])
      $httpBackend.expectGET(url).respond('{"model": [{"id": "' + MODEL_ID + '"}]}')

      $rootScope.goSection(['features'])
      $httpBackend.flush()

    xit "should load tests", inject () ->
      url = BASE_URL + MODEL_ID + '/tests/?show=' + encodeURIComponent('name,created_on,status,parameters,accuracy,examples_count,created_by')
      $httpBackend.expectGET(url).respond('{"tests": []}')

      $rootScope.LOADED_SECTIONS.push 'main'

      $rootScope.goSection(['test'])
      $httpBackend.flush()

    # TODO: solve the issue with "TypeError: 'undefined' is not an object (evaluating 'fn.apply')"
    xit "should send tags update query", inject () ->
      url = BASE_URL + MODEL_ID + '/tests/?show=' + encodeURIComponent('name,
created_on,status,parameters,accuracy,examples_count,created_by')
      $httpBackend.expectPUT(url).respond('{"tests": []}')

      $rootScope.model = Model({
        id: MODEL_ID,
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
      # TODO: nader20140708 : I don't if scope should have data object from elsewhere !
      # but looks like formElements has changed to be data
      $rootScope.data = {}

      createController "BaseModelDataSetActionCtrl"

      expect($rootScope.select2Options).toBeDefined()
      expect(_.keys($rootScope.data).length).toBeGreaterThan(2)

  describe "ModelActionsCtrl", ->

    # TODO: solve the issue with "TypeError: 'undefined' is not an object (evaluating 'fn.apply')"
    xit "should call upload_predict action", inject () ->
      createController "ModelActionsCtrl"

      url = BASE_URL + MODEL_ID + '/action/upload_predict/'
      $httpBackend.expectPUT(url).respond('{"model": {"id": 1, "name": "Name", "status": "Trained"}}')

      model = Model({
        id: MODEL_ID,
        name: 'Model1',
        status: 'New',
        features: '',
        weights_synchronized: true
      })

      $rootScope.uploadModelToPredict(model)
