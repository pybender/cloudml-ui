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

        $rootScope.paramsConfig = {"str_param": {"type": "str"}}
        $rootScope.requiredParams = ["str_param"]
        $rootScope.optionalParams = []

        # invlaid
        $rootScope.params = {}
        element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
  params-config="paramsConfig"
  required-params="requiredParams"
  optional-params="optionalParams"></parameters-editor>
</form>
""")($rootScope)
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        # valid
        $rootScope.params = {"str_param": "value"}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe true
        expect($rootScope.myForm.$valid).toBe true

        expect(element.html()).toContain('<div class="jsonContents ng-scope">')
        expect(element.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
        expect(element.html()).toContain('>str_param</label>')

    it "should create parameters editor control with object parameter", ->
      inject ($compile, $rootScope) ->

        $rootScope.paramsConfig = {"map_param": {"type": "dict"}}
        $rootScope.requiredParams = ["map_param"]
        $rootScope.optionalParams = []

        # invlaid
        $rootScope.params = {}
        element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
  params-config="paramsConfig"
  required-params="requiredParams"
  optional-params="optionalParams"></parameters-editor>
</form>
""")($rootScope)
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        # valid
        $rootScope.params = {map_param: {one: 'one_val', two: 'two_val'}}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe true
        expect($rootScope.myForm.$valid).toBe true

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

        # invlaid
        $rootScope.params = {}
        element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
  params-config="paramsConfig"
  required-params="requiredParams"
  optional-params="optionalParams"></parameters-editor>
</form>
""")($rootScope)
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        # invalid json
        $rootScope.params = {text_param: 'invalid{"key":"value"}json'}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        # valid
        $rootScope.params = {text_param: '{"key":"value"}'}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe true
        expect($rootScope.myForm.$valid).toBe true

        expect(element.html()).toContain('<div class="jsonContents ng-scope">')
        expect(element.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
        expect(element.html()).toContain('>text_param</label>')
        expect(element.html()).toContain('<textarea name="text_param" ng-model="paramsEditorData[key]"')

    it "should validate items", ->
      inject ($compile, $rootScope) ->
        """
        Attention: As of Anguular 1.2.20 no need to call validate exciplictly
        as calling scope.digest() implicitly calls the validate
        """
        $rootScope.paramsConfig = {
          "str_param": {"type": "str"},
          "map_param": {"type": "dict"},
          "text_param": {"type": "text"}
        }
        $rootScope.requiredParams = ["str_param", "map_param", "text_param"]
        $rootScope.optionalParams = []

        # empty params
        $rootScope.params = {}
        $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
  params-config="paramsConfig"
  required-params="requiredParams"
  optional-params="optionalParams"></parameters-editor>
</form>
""")($rootScope)
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams = ->
          $rootScope.params =
            map_param: {one: 'one_val', two: 'two_val'}
            str_param: "value"
            text_param: '{"key": "value"}'
          $rootScope.$digest()
          expect($rootScope.myForm.params.$valid).toBe true
          expect($rootScope.myForm.$valid).toBe true

        buildValidParams()
        $rootScope.params.map_param = {one: '', two: 'two_val'}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        $rootScope.params.map_param = {}
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        delete $rootScope.params['map_param']
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        $rootScope.params.str_param = ""
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        delete $rootScope.params['str_param']
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        $rootScope.params.text_param = 'wrong{"key": "value"}json'
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        $rootScope.params.text_param = ""
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

        buildValidParams()
        delete $rootScope.params['text_param']
        $rootScope.$digest()
        expect($rootScope.myForm.params.$valid).toBe false
        expect($rootScope.myForm.$valid).toBe false

    # TODO: nader20140817: we need to work on adding new item after adopting
    # isloate scopes
    xit "should correctly add a new string item to object", ->
      inject ($compile, $rootScope) ->

        $rootScope.paramsConfig = {"map_param": {"type": "dict"}}
        $rootScope.requiredParams = ["map_param"]
        $rootScope.optionalParams = []

        $rootScope.params = {map_param: {one: 'one_val', two: 'two_val'}}
        element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
  params-config="paramsConfig"
  required-params="requiredParams"
  optional-params="optionalParams"></parameters-editor>
</form>
""")($rootScope)
        $rootScope.$digest()

        addItem = angular.element(element.children().children()[0]).scope().addItem
        $rootScope.keyName = 'new_key'
        $rootScope.valueName = 'new_value'
        $rootScope.valueType = 'str'

        obj = {}
        addItem(obj)

        expect(obj.new_key).toEqual('new_value')

  describe "loadindicator", ->

    it "should create progress", inject(($compile, $rootScope) ->
      element = $compile("""
<loadindicator title="Adding model..." cml-progress="savingProgress"></loadindicator>
""")($rootScope)

      $rootScope.savingProgress = '0%'
      $rootScope.$digest()
      expect(element.html()).toContain('<div class="progress progress-striped active">')
      expect(element.html()).toContain('class="bar"')
      expect(element.html()).toContain('width: 0%;')

      $rootScope.savingProgress = '10%'
      $rootScope.$digest()
      expect(element.html()).toContain('class="bar"')
      expect(element.html()).toContain('width: 10%;')
    )


    it "should create spinner", inject(($compile, $rootScope) ->
      element = $compile("""
<loadindicator title="Adding model..."></loadindicator>
""")($rootScope)

      $rootScope.$digest()
      expect(element[0].outerHTML).toContain('loading-indicator-spin')
      expect(element.html()).toContain('<img src="/img/ajax-loader.gif">')
    )
