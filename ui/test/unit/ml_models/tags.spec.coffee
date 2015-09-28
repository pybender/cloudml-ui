'use strict'

# Unittests for Tags related controllers

describe "ML Models Tags Controllers", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.controllers")

  beforeEach(module "app.importhandlers.models")
  beforeEach(module "app.importhandlers.xml.models")
  beforeEach(module "app.datasets.model")

  beforeEach(module "app.features.models")
  beforeEach(module "app.models.controllers")
  beforeEach(module "app.models.model")

  $httpBackend = null
  $rootScope = null
  $scope = null
  settings = null
  $routeParams = null
  createController = null
  $location = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe 'TagCtrl', ->

    it  'should init scope with current tag', ->
      $location.search {tag: 'zozo'}
      createController 'TagCtrl'
      expect($scope.currentTag).toEqual 'zozo'

  describe "TagCloudCtrl", ->
    @base_url = null
    @tags_url = null
    @tags_resp = null
    @tags = null
    @fields = null

    beforeEach(inject((Tag) ->
      tag1 = new Tag
        id: 1
        text: 'simple'
        count: 10
      tag2 = new Tag
        id: 2
        text: 'complex'
        count: 3

      @base_url = tag1.BASE_API_URL
      @fields = ['text', 'count']
      @tags_url = @base_url + '?show=' + @fields.join(',')
      @tags = [tag1, tag2]
      @tags_resp = buildListResponse(@tags, @fields)
    ))

    it "should make tag list query", ->
      $httpBackend.expectGET(@tags_url)
      .respond(@tags_resp)

      createController "TagCloudCtrl"
      $httpBackend.flush()

      for tag, i in @tags
        expect($scope.tag_list[i].text).toBe(@tags[i].text)
        expect($scope.tag_list[i].count).toBe(@tags[i].count)
        expect($scope.tag_list[i].id).toBe(@tags[i].id)

    it "should loading tag list error message", ->
      $scope.setError = jasmine.createSpy '$scope.setError'
      $httpBackend.expectGET @tags_url
      .respond 400
      createController 'TagCloudCtrl'
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()
      expect($scope.tag_list).toBeUndefined()
