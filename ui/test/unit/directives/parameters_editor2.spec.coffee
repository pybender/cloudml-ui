'use strict'

# jasmine specs for directives go here
describe "directives/parametersEditor", ->

  $compile = null
  $rootScope = null
  $scope = null
  $provide = null
  $httpBackend = null
  $window = null

  elem = null
  afterEach ->
    if elem
      elem.remove()

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
      $httpBackend = $injector.get('$httpBackend')
      $window = $injector.get('$window')
      $window.alert = jasmine.createSpy '$window.alert'
      $window.confirm = jasmine.createSpy('$window.confirm')

  xdescribe 'dynamicName', ->

    it 'should change the name of the input based on the set dynamic name', ->
      $scope = $rootScope.$new()

      $scope.inputValue = 'zinger'
      $scope.filedName = 'theField'

      html = """
        <form name="myForm">
          <input type="text" ng-model="inputValue" ng-model-onblur
          dynamic-name="filedName"/>
        </form>
        """
      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()

      input = $('input', elem)
      expect(input.length).toBe 1
      expect(input.attr('name')).toEqual 'theField'
      expect(input.attr('dynamic-name')).toBeUndefined()
      expect(input.val()).toEqual 'zinger'
      expect($scope.myForm.theField.$viewValue).toEqual 'zinger'

      # setting the value
      input.val('zozo')
      input.change()
      $scope.$digest()

      expect(input.val()).toEqual 'zozo'
      expect($scope.myForm.theField.$viewValue).toEqual 'zozo'
      expect($scope.inputValue).toEqual 'zozo'


  xdescribe 'parameterValidator', ->

    createContext = (value, field)->
      $scope = $rootScope.$new()

      $scope.inputValue = value
      $scope.field = field

      html = """
        <form name="myForm">
        <input type="text" ng-model="inputValue" name="theField"
        parameter-validator=""/>
         </form>
        """
      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()

    it 'should validate a required int field', ->

      createContext 'zozo',
        {type: 'int', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val('123')
      input.change()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('')
      input.change()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val('xyz')
      input.change()

      expect($scope.inputValue).toEqual 'xyz'
      expect($scope.myForm.theField.$viewValue).toEqual 'xyz'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

    it 'should validate a not required int field', ->

      createContext 'zozo',
        {type: 'int', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val('123')
      input.change()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('')
      input.change()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('xyz')
      input.change()

      expect($scope.inputValue).toEqual 'xyz'
      expect($scope.myForm.theField.$viewValue).toEqual 'xyz'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

    it 'should validate a required str field', ->

      createContext '',
        {type: 'str', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val('abc')
      input.change()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('')
      input.change()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

    it 'should validate a not required str field', ->

      createContext '',
        {type: 'str', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('abc')
      input.change()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('')
      input.change()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

    it 'should validate a required text/json field', ->

      createContext '',
        {type: 'text', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val('abc')
      input.change()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val(angular.toJson({some: 'json'}))
      input.change()

      expect($scope.inputValue).toEqual angular.toJson({some: 'json'})
      expect($scope.myForm.theField.$viewValue).toEqual angular.toJson({some: 'json'})
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

    it 'should validate a not required text/json field', ->

      createContext '',
        {type: 'text', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      input.val('abc')
      input.change()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      input.val(angular.toJson({some: 'json'}))
      input.change()

      expect($scope.inputValue).toEqual angular.toJson({some: 'json'})
      expect($scope.myForm.theField.$viewValue).toEqual angular.toJson({some: 'json'})
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

  describe 'parametersEditor2', ->

    editorScope = null

    createDirective = (html)->
      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()
      editorScope = $('>parameters-editor2', elem).children().scope()

    createContext = (feature)->
      $scope = $rootScope.$new()
      $scope.feature = feature
      $scope.configuration = getConfiguration()

    prepareContext = (feature, html)->
      createContext feature
      createDirective html


    describe 'adding new feature', ->

      for type in ['text', 'float', 'numeric', 'int', 'boolean']
        do (type)->
          it "should handle simple types: #{type}", ->
            prepareContext {type: type, params: {}}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.params"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
            expect($scope.hasNoFields).toBe true
            expect(_.isEmpty(editorScope.fields)).toBe true
            noParamsMsg = $('i[ng-show="hasNoFields"]')
            expect(noParamsMsg.length).toBe 1
            expect(noParamsMsg.hasClass('ng-hide')).toBe false
            expect($('div[class="jsonContents"]').children().length).toBe 0

      for type in [{name: 'regex', count: 1}, {name: 'map', count: 1},
        {name: 'categorical', count: 2}, {name: 'composite', count: 1},
        {name: 'categorical_label', count: 2}, {name: 'date', count: 1}]
        do (type)->
          it "should handle complex types: #{type.name}", ->
            prepareContext {type: type.name, params: {}}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.params"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
            expect($scope.hasNoFields).toBe false
            expect(_.isEmpty(editorScope.fields)).toBe false
            noParamsMsg = $('i[ng-show="hasNoFields"]')
            expect(noParamsMsg.length).toBe 1
            expect(noParamsMsg.hasClass('ng-hide')).toBe true
            expect($('div[class="jsonContents"]').children().length).toBe type.count

      it 'should handle switching back and forth between simple and complex types', ->

        prepareContext {type: 'int', params: {}}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.params"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """

        expect($scope.hasNoFields).toBe true
        expect(_.isEmpty(editorScope.fields)).toBe true
        noParamsMsg = $('i[ng-show="hasNoFields"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe false

        $scope.feature.type = 'categorical'
        $scope.$digest()

        expect($scope.hasNoFields).toBe false
        expect(_.isEmpty(editorScope.fields)).toBe false
        noParamsMsg = $('i[ng-show="hasNoFields"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe true

        $scope.feature.type = 'boolean'
        $scope.$digest()

        expect($scope.hasNoFields).toBe true
        expect(_.isEmpty(editorScope.fields)).toBe true
        noParamsMsg = $('i[ng-show="hasNoFields"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe false


      xit "should create parameters editor control with string parameter", ->

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

    getConfiguration = ->
      return {
      params:
        pattern:
          help_text: 'Please enter a pattern'
          type: 'str'
        chain:
          help_text: 'Please enter valid json'
          type: 'text'
        mappings:
          help_text: 'Please add parameters to dictionary'
          type: 'dict'
        split_pattern:
          help_text: 'Please enter a pattern'
          type: 'str'
        min_df:
          help_text: 'Please enter a int value'
          type: 'int'
      defaults:
        date: 946684800
      types:
        regex:
          optional_params: []
          type: ''
          default_params: []
          required_params: ['pattern']
        map:
          optional_params: []
          type: ''
          default_params: []
          required_params: ['mappings']
        categorical:
          optional_params: ['split_pattern', 'min_df']
          type: ''
          default_params: []
          required_params: []
        composite:
          optional_params: []
          type: ''
          default_params: []
          required_params: ['chain']
        text:
          optional_params: []
          type: "<type 'str'>"
          default_params: []
          required_params: []
        float:
          optional_params: []
          type: "<type 'float'>"
          default_params: []
          required_params: []
        numeric:
          optional_params: []
          type: "<type 'float'>"
          default_params: []
          required_params: []
        int:
          optional_params: []
          type: "<type 'int'>"
          default_params: []
          required_params: []
        categorical_label:
          optional_params: ['split_pattern', 'min_df']
          type: ''
          default_params: []
          required_params: []
        boolean:
          optional_params: []
          type: "<type 'bool'>"
          default_params: []
          required_params: []
        date:
          optional_params: []
          type: ''
          default_params: []
          required_params: ['pattern']
      }
