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

  describe "parameters-editor", ->

    it "should create parameters editor control with string parameter", ->
      inject ($compile, $rootScope) ->
        $rootScope.params = {"str_param": "value"}

        $rootScope.paramsConfig = {"str_param": {"type": "str"}}
        $rootScope.requiredParams = ["str_param"]
        $rootScope.optionalParams = []

        element = $compile('<parameters-editor ng-model="params"></parameters-editor>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<div class="jsonContents ng-scope">')
        expect(element.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
        expect(element.html()).toContain('>str_param</label>')

    it "should create parameters editor control with object parameter", ->
      inject ($compile, $rootScope) ->
        $rootScope.params = {
          "map_param": {one: 'one_val', two: 'two_val'}
        }

        $rootScope.paramsConfig = {"map_param": {"type": "dict"}}
        $rootScope.requiredParams = ["map_param"]
        $rootScope.optionalParams = []

        element = $compile('<parameters-editor ng-model="params"></parameters-editor>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<div class="jsonContents ng-scope">')
        expect(element.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
        expect(element.html()).toContain('>map_param</label>')
        expect(element.html()).toContain('<a title="add new parameter" ng-click="$parent.showAddKey = true"')

    it "should create parameters editor control with text parameter", ->
      inject ($compile, $rootScope) ->
        $rootScope.params = {
          "text_param": '{"key": "val"}'
        }

        $rootScope.paramsConfig = {"text_param": {"type": "text"}}
        $rootScope.requiredParams = ["text_param"]
        $rootScope.optionalParams = []

        element = $compile('<parameters-editor ng-model="params"></parameters-editor>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<div class="jsonContents ng-scope">')
        expect(element.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
        expect(element.html()).toContain('>text_param</label>')
        expect(element.html()).toContain('<textarea name="params" ng-model="paramsEditorData[key]"')

    it "should validate items", ->
      inject ($compile, $rootScope) ->
        $rootScope.params = {}

        $rootScope.paramsConfig = {
          "str_param": {"type": "str"},
          "map_param": {"type": "dict"},
          "text_param": {"type": "text"}
        }
        $rootScope.requiredParams = ["str_param", "map_param", "text_param"]
        $rootScope.optionalParams = []

        $compile('<form name="form">
<parameters-editor ng-model="params" name="params"></parameters-editor>
</form>')($rootScope)
        $rootScope.$digest()

        $rootScope.params = {"map_param": {one: 'one_val', two: 'two_val'}}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(true);

        $rootScope.params = {"map_param": {one: '', two: 'two_val'}}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(false);

        $rootScope.params = {"map_param": {}}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(false);

        $rootScope.params = {"str_param": "value"}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(true);

        $rootScope.params = {"str_param": ""}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(false);

        $rootScope.params = {"text_param": '{"key": "value"}'}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(true);

        $rootScope.params = {"text_param": 'wrong{"key": "value"}json'}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(false);

        $rootScope.params = {"text_param": ""}
        $rootScope.$digest()
        $rootScope.validate()
        expect($rootScope.form.params.$valid).toBe(false);

    it "should correctly add a new string item to object", ->
      inject ($compile, $rootScope) ->
        $rootScope.params = {
          "map_param": {one: 'one_val', two: 'two_val'}
        }

        $rootScope.paramsConfig = {"map_param": {"type": "dict"}}
        $rootScope.requiredParams = ["map_param"]
        $rootScope.optionalParams = []

        element = $compile('<parameters-editor ng-model="params"></parameters-editor>')($rootScope)
        $rootScope.$digest()

        addItem = $rootScope.addItem
        $rootScope.keyName = 'new_key'
        $rootScope.valueName = 'new_value'
        $rootScope.valueType = 'str'

        obj = {}
        addItem(obj)

        expect(obj.new_key).toEqual('new_value')
