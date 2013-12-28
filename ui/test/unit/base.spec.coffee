'use strict'

# jasmine specs for base model go here

describe "base", ->

  beforeEach(module "ngCookies")
  beforeEach(module "app.base")

  $httpBackend = null
  settings = null
  model = null

  beforeEach(inject(($injector, BaseModel) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')

    BaseModel.prototype.BASE_API_URL = 'http://host/api/objects/'
    BaseModel.prototype.MAIN_FIELDS = ['id', 'name']
    BaseModel.prototype.DEFAULT_FIELDS_TO_SAVE = ['name']
    model = new BaseModel({id: 'someid'})
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )

  describe "BaseModel", ->
    it "should load model from JSON", inject(() ->
      model.loadFromJSON({name: 'somename'})
      expect(model.name).toEqual('somename')
      expect(model.id).toEqual('someid')
      expect(model.other).toBeUndefined()
    )

    it "should load list of objects", inject((BaseModel) ->
      $httpBackend.expectGET('http://host/api/objects/?one=val1&two=val2')
      .respond('{"objects": [{"name": "loaded name"}]}')

      objects = null

      BaseModel.$loadAll({one: 'val1', two: 'val2'}).then((resp) =>
        objects = resp.objects
      )
      $httpBackend.flush()

      expect(objects[0].name).toEqual('loaded name')
    )

    it "should load single object", inject(() ->
      $httpBackend.expectGET('http://host/api/objects/someid/?one=val1&two=val2')
      .respond('{"object": {"name": "loaded name"}}')

      model.$load({one: 'val1', two: 'val2'})
      $httpBackend.flush()

      expect(model.name).toEqual('loaded name')
    )

    it "should save existing object", inject(() ->
      $httpBackend.expectPUT('http://host/api/objects/someid/?')
      .respond('{}')

      model.name = 'saved name'
      model.$save({one: 'val1', two: 'val2'})
      $httpBackend.flush()

      expect(model.loaded).toBe(true)
    )

    it "should save new object", inject((BaseModel) ->
      # TODO: avoid of '/null/'
      $httpBackend.expectPOST('http://host/api/objects/null/?')
      .respond('{}')

      model = new BaseModel({id: null})
      model.name = 'saved name'
      model.$save({one: 'val1', two: 'val2'})
      $httpBackend.flush()

      expect(model.loaded).toBe(true)
    )

    it "should delete object", inject(() ->
      $httpBackend.expectDELETE('http://host/api/objects/someid/')
      .respond('{}')

      model.$delete()
      $httpBackend.flush()
    )
