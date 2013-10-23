'use strict'

# jasmine specs for directives go here
describe "directives", ->

  beforeEach(module "app.directives")

  describe "app-version", ->

    it "should print current version", ->
      module ($provide) ->
        $provide.value "version", "TEST_VER"
        return

      inject ($compile, $rootScope) ->
        element = $compile("<span app-version></span>")($rootScope)
        expect(element.text()).toEqual "TEST_VER"

  describe "json-editor", ->

    it "should create json editor control for object", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {"str_param": "value"}

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<span class="jsonObjectKey">')
        expect(element.html()).toContain('<span ng-switch-default="" class="jsonLiteral ng-scope">')
        expect(element.html()).toContain('<input type="text" ng-model="item[key]" placeholder="Empty" class="ng-pristine ng-valid">')
        expect(element.html()).toNotContain('<ol class="arrayOl ng-pristine ng-valid" ng-model="item">')

    it "should create json editor control for array", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = ["one", "two", "three"]

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<ol class="arrayOl ng-pristine ng-valid" ng-model="item">')

    it "should correctly determine object's type", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {}

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        getType = element.scope().$$childTail.getType

        expect(getType('Some string')).toEqual('str')
        expect(getType(["one", "two", "three"])).toEqual('list')
        expect(getType({"str_param": "value"})).toEqual('dict')
        expect(getType(undefined)).toEqual('str')
        expect(getType(null)).toEqual('str')

    it "should correctly add a new string item to object", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {}

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        localScope = element.scope().$$childTail
        addItem = localScope.addItem
        localScope.keyName = 'new_key'
        localScope.valueName = 'new_value'
        localScope.valueType = 'str'

        obj = {}
        addItem(obj)

        expect(obj.new_key).toEqual('new_value')

    it "should correctly add a new object item to object", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {}

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        localScope = element.scope().$$childTail
        addItem = localScope.addItem
        localScope.keyName = 'new_key'
        localScope.valueType = 'dict'

        obj = {}
        addItem(obj)

        expect(obj.new_key).toEqual({})

    it "should correctly add a new string item to array", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = []

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        localScope = element.scope().$$childTail
        addItem = localScope.addItem
        localScope.valueName = 'new_value'
        localScope.valueType = 'str'

        obj = []
        addItem(obj)

        expect(obj[0]).toEqual('new_value')

    it "should correctly add a new object item to array", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = []

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        localScope = element.scope().$$childTail
        addItem = localScope.addItem
        localScope.valueName = 'new_value'
        localScope.valueType = 'dict'

        obj = []
        addItem(obj)

        expect(obj[0]).toEqual({})

    it "should completely apply configuration", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {}
        $rootScope.params_config = {
          mappings: {
            type: 'dict',
            help_text: 'This is map parameter'
          },
          pattern: {
            type: 'str',
            help_text: 'Please enter a valid regular expression'
          },
          'some composite': {
            type: 'list',
            help_text: 'This is composite parameter'
          }
        }

        element = $compile('<div><json-editor item="jsonVal" config="params_config"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        valueTypes = element.scope().$$childTail.valueTypes

        expect(valueTypes[0].name).toEqual('mappings')
        expect(valueTypes[0].type).toEqual('dict')
        expect(valueTypes[1].name).toEqual('pattern')
        expect(valueTypes[1].type).toEqual('str')
        expect(valueTypes[2].name).toEqual('some composite')
        expect(valueTypes[2].type).toEqual('list')
