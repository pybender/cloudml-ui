'use strict'

# jasmine specs for models

describe "models", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
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
  $modal = null
  createController = null
  Model = null

  MODEL_ID = '5566'
  BASE_URL = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $modal = $injector.get('$modal')
    Model = $injector.get('Model')

    BASE_URL = settings.apiUrl + 'models/'

    spyOn($location, 'path')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $rootScope }
      $controller(ctrl, injected)
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
      url = settings.apiUrl + 'tags/?show=' + 'text,count'
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
      url = settings.apiUrl + 'tags/?show=' + 'text,id'
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

    it "should make details request", inject (MODEL_FIELDS, FIELDS_BY_SECTION) ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + MODEL_FIELDS + ',' + FIELDS_BY_SECTION['model']
      $httpBackend.expectGET(url)
      .respond.apply @, map_url_to_response(url, 'multiclass model main fields')

      s3_url = "#{BASE_URL}#{$rootScope.model.id}/action/trainer_download_s3url/"
      $httpBackend.expectGET(s3_url)
      .respond """
{"trainer_file_for": #{MODEL_ID}, "url": "https://.s3.amazonaws.com/9c4012780c0111e4968b000c29e3f35c?Signature=%2FO7%2BaUv4Fk84ioxWigRwkcdgVM0"}
"""

      $rootScope.goSection(['model'])
      $httpBackend.flush()
      expect($rootScope.model.trainer_s3_url).toEqual 'https://.s3.amazonaws.com/9c4012780c0111e4968b000c29e3f35c?Signature=%2FO7%2BaUv4Fk84ioxWigRwkcdgVM0'

    it "should request only features", inject (FIELDS_BY_SECTION) ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + FIELDS_BY_SECTION['main']
      $httpBackend.expectGET(url).respond('{"model": [{"id": "' + MODEL_ID + '"}]}')

      $rootScope.goSection(['features'])
      $httpBackend.flush()
