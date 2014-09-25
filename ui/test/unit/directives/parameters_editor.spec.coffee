'use strict'

# jasmine specs for directives go here
describe "directives/parametersEditor", ->

  $compile = null
  $rootScope = null
  $scope = null
  $provide = null
  $httpBackend = null
  $window = null

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'
    module 'ui.codemirror'

    module 'app.base'
    module "app.directives"
    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.datasets.model'
    module 'app.features.models'
    module 'app.templates' # to serve partials html
    module 'app.filters'

    module 'app.services', ($provide) ->
      $provide.value "version", "TEST_VER"
      return

    inject ($injector) ->
      $rootScope = $injector.get('$rootScope')
      $compile = $injector.get('$compile')
      $scope = $rootScope.$new()
      $httpBackend = $injector.get('$httpBackend')
      $window = $injector.get('$window')
      $window.alert = jasmine.createSpy '$window.alert'
      $window.confirm = jasmine.createSpy('$window.confirm')

  describe "parametersEditor", ->

    elem = null
    innerScope = null
    afterEach ->
      if elem
        elem.remove()

    prepareContext = (html)->
      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()
      innerScope = $('>parameters-editor', elem).children().scope()

    it "should create parameters editor control with string parameter", ->

      $scope.paramsConfig = {"str_param": {"type": "str"}, strange: {type: null}}
      $scope.requiredParams = ["str_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # get type -- we are doing it here to be able to get the invalid type strange
      expect(innerScope.getType 'str_param').toEqual 'str'
      expect(innerScope.getType 'zinger').toEqual 'str'
      expect(innerScope.getType 'strange').toEqual 'str'

      # valid
      $scope.paramsConfig = {"str_param": {"type": "str"}}
      $scope.params = {"str_param": "value"}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>str_param</label>')

      # toggle collapse
      expect($scope.collapsed).toBeUndefined()
      innerScope.toggleCollapse()
      expect(innerScope.collapsed).toBe true
      expect(innerScope.chevron).toEqual 'icon-chevron-right'
      innerScope.toggleCollapse()
      expect(innerScope.collapsed).toBe false
      expect(innerScope.chevron).toEqual 'icon-chevron-down'


    it "should manipulate parameters", ->

      $scope.paramsConfig = {"str_param": {"type": "str"}, "dict_param": {"type": "dict"}}
      $scope.requiredParams = ["str_param"]
      $scope.optionalParams = []

      $rootScope.showAddKey = true
      $scope.params = {str_param: 'some string', dict_param: {}}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      expect(innerScope.isTopLevel()).toEqual true

      # moving str_param to dict_param will delete dict_param
      innerScope.moveKey innerScope.paramsEditorData, 'str_param', 'dict_param'
      expect(innerScope.paramsEditorData).toEqual {dict_param: 'some string'}

      # resetting
      $scope.params = {str_param: 'some string', dict_param: {}}
      $scope.$digest()

      # trying to delete required parameter fails
      innerScope.deleteKey innerScope.paramsEditorData, 'str_param'
      expect(innerScope.isRequired 'str_param').toBe true
      expect($window.alert).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string', dict_param: {}}

      # trying to delete non-required parameter and confirm false
      innerScope.deleteKey innerScope.paramsEditorData, 'dict_param'
      expect(innerScope.isRequired 'dict_param').toBe false
      expect($window.confirm).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string', dict_param: {}}

      # trying to delete non-required parameter and confirm true
      $window.confirm.and.returnValue true
      innerScope.deleteKey innerScope.paramsEditorData, 'dict_param'
      expect(innerScope.isRequired 'dict_param').toBe false
      expect($window.confirm).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string'}

      # adding item no key name
      innerScope.addItem innerScope.paramsEditorData
      expect($window.alert).toHaveBeenCalledWith 'Please fill in a name'

# TODO: nader20140912, continue adding new parameter logic
#      # adding item key name supplied, the click to trigger showAddKey = true
#      # there are two, we don't care which
#      expect($('a', elem).attr('title')).toEqual 'add new parameter'
#      $('a', elem).click()
#
#      expect($('.input-small .addItemKeyInput', elem).length).toEqual 1
#      expect($('.input-medium .addItemValueInput', elem)).length.toEqual 1
#      $('.input-small .addItemKeyInput', elem).val 'new key to test'
#      $('.input-medium .addItemValueInput', elem).val 'new key to test'
#      $('a', elem).scope().addItem innerScope.paramsEditorData
#      expect(innerScope.paramsEditorData).toEqual ''


    it "should create parameters editor control with object parameter", ->

      $scope.paramsConfig = {"map_param": {"type": "dict"}}
      $scope.requiredParams = ["map_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # valid
      $scope.params = {map_param: {one: 'one_val', two: 'two_val'}}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>map_param</label>')
      expect(elem.html()).toContain('<a title="add new parameter" ng-click="$parent.showAddKey = true"')

    it "should create parameters editor control with text parameter", ->
      $scope.params = {
        "text_param": '{"key": "val"}'
      }

      $scope.paramsConfig = {"text_param": {"type": "text"}}
      $scope.requiredParams = ["text_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # invalid json
      $scope.params = {text_param: 'invalid{"key":"value"}json'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # valid
      $scope.params = {text_param: '{"key":"value"}'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>text_param</label>')
      expect(elem.html()).toContain('<textarea name="text_param" ng-model="paramsEditorData[key]"')

    # TODO: this test takes too long
    it "should validate items", ->
      """
      Attention: As of Anguular 1.2.20 no need to call validate exciplictly
      as calling scope.digest() implicitly calls the validate
      """
      $scope.paramsConfig = {
        "str_param": {"type": "str"},
        "map_param": {"type": "dict"},
        "text_param": {"type": "text"}
      }
      $scope.requiredParams = ["str_param", "map_param", "text_param"]
      $scope.optionalParams = []

      # empty params
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams = ->
        $scope.params =
          map_param: {one: 'one_val', two: 'two_val'}
          str_param: "value"
          text_param: '{"key": "value"}'
        $scope.$digest()
        expect($scope.myForm.params.$valid).toBe true
        expect($scope.myForm.$valid).toBe true

      buildValidParams()
      $scope.params.map_param = {one: '', two: 'two_val'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.map_param = {}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['map_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.str_param = ""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['str_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.text_param = 'wrong{"key": "value"}json'
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.text_param = ""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['text_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

    # TODO: nader20140817: we need to work on adding new item after adopting
    # isloate scopes
    xit "should correctly add a new string item to object", ->

      $scope.paramsConfig = {"map_param": {"type": "dict"}}
      $scope.requiredParams = ["map_param"]
      $scope.optionalParams = []

      $scope.params = {map_param: {one: 'one_val', two: 'two_val'}}
      element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
""")($scope)
      $scope.$digest()

      addItem = angular.element(element.children().children()[0]).scope().addItem
      $scope.keyName = 'new_key'
      $scope.valueName = 'new_value'
      $scope.valueType = 'str'

      obj = {}
      addItem(obj)

      expect(obj.new_key).toEqual('new_value')
