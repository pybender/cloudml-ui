'use strict'

# jasmine specs for awsinstances

describe "awsinstances", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ngRoute")
  beforeEach(module "app.config")
  beforeEach(module "app.services")
  beforeEach(module "app.base")

  beforeEach(module "app.awsinstances.model")
  beforeEach(module "app.awsinstances.controllers")

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  createController = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')

    createController = (ctrl) ->
       $controller(ctrl, {'$scope' : $rootScope })
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "AwsInstanceListCtrl", ->

    it "should make list query", inject () ->
      fields = ['name','type','created_on','updated_on','ip','is_default',
                'created_by','updated_by'].join(',')
      url = settings.apiUrl + 'aws_instances/?show=' + encodeURIComponent(fields)
      $httpBackend.expectGET(url).respond('{"instances": []}')

      createController "AwsInstanceListCtrl"

      $httpBackend.flush()

  describe "InstanceActionsCtrl", ->

    it "should send save query", inject (AwsInstance) ->
      id = '5224de2907dbec210daec24e'

      url = settings.apiUrl + 'aws_instances/' + id + '/?'
      $httpBackend.expectPUT(url).respond('{"instance": []}')

      instance = new AwsInstance({
        id: id,
        is_default: false,
        type: {'name': 'some'}
      })

      createController "InstanceActionsCtrl"
      $rootScope.makeDefault(instance)

      $httpBackend.flush()

  describe "AwsInstanceDetailsCtrl", ->

    it "should make details query", inject () ->
      id = '5224de2907dbec210daec24e'
      fields = ['name','type','created_on','updated_on','ip','description',
                'is_default','created_by'].join(',')

      url = settings.apiUrl + 'aws_instances/' + id + '/?show=' + encodeURIComponent(fields)
      $httpBackend.expectGET(url).respond('{"instance": {}}')

      $routeParams.id = id
      createController "AwsInstanceDetailsCtrl"
      $httpBackend.flush()

      expect($rootScope.instance.id).toBe(id)

  describe "GetInstanceCtrl", ->

    it "should make list query and activate the section", inject () ->
      fields = "name,id,ip,is_default"
      url = settings.apiUrl + 'aws_instances/?show=' + encodeURIComponent(fields)
      $httpBackend.expectGET(url).respond('{"instances": []}')

      createController "GetInstanceCtrl"
      $httpBackend.flush()

  describe "SpotInstanceRequestCtrl", ->

    it "should make no requests but define types", inject () ->
      createController "SpotInstanceRequestCtrl"

      expect($rootScope.types).toBeDefined()
