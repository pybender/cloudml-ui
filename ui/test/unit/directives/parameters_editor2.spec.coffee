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

  changeElemValue = (elem, val)->
    elem.val(val)
    elem.change()
    elem.trigger('blur')

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

  describe 'dynamicName', ->

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
      changeElemValue(input, 'zozo')
      $scope.$digest()

      expect(input.val()).toEqual 'zozo'
      expect($scope.myForm.theField.$viewValue).toEqual 'zozo'
      expect($scope.inputValue).toEqual 'zozo'


  describe 'parameterValidator', ->

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

      changeElemValue input, '123'
      $scope.$digest()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      changeElemValue input, 'xyz'
      $scope.$digest()

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

      changeElemValue input, '123'
      $scope.$digest()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      changeElemValue input, 'xyz'
      $scope.$digest()

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

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      changeElemValue input, ''
      $scope.$digest()

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

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe true
      expect($scope.myForm.theField.$invalid).toBe false

      changeElemValue input, ''
      $scope.$digest()

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

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      changeElemValue input, angular.toJson({some: 'json'})
      $scope.$digest()

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

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expect($scope.field.valid).toBe false
      expect($scope.myForm.theField.$invalid).toBe true

      changeElemValue input, angular.toJson({some: 'json'})
      $scope.$digest()

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


    describe 'simple and complex types with switching', ->

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

    describe 'handling complex types with different parameter types', ->

      testCategorical = (params)->
        prepareContext {type: 'categorical', params: params}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.params"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """
        inputs = $('input', elem)
        textareas = $('textarea', elem)
        expect(inputs.length).toBe 2
        expect(textareas.length).toBe 0

        min_df_input = $('input[name="min_df"]', elem)
        split_pattern_input = $('input[name="split_pattern"]', elem)

        expect(min_df_input.length).toBe 1
        expect(split_pattern_input.length).toBe 1

        if not _.isEmpty(params)
          expect(min_df_input.val()).toEqual params.min_df + ''
          expect(split_pattern_input.val()).toEqual params.split_pattern

        changeElemValue min_df_input, '123'
        $scope.$digest()
        changeElemValue split_pattern_input, 'zozo'
        $scope.$digest()

        expect($scope.feature.params).toEqual {min_df: '123', split_pattern: 'zozo'}

        changeElemValue min_df_input, 'abc'
        $scope.$digest()
        expect($scope.feature.params).toEqual {min_df: 'abc', split_pattern: 'zozo'}

      testComposite = (params)->
        prepareContext {type: 'composite', params: params}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.params"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """
        inputs = $('input', elem)
        textareas = $('textarea', elem)
        expect(inputs.length).toBe 0
        expect(textareas.length).toBe 1

        chain_textarea = $('textarea[name="chain"]', elem)

        expect(chain_textarea.length).toBe 1

        if not _.isEmpty(params)
          expect(chain_textarea.val()).toEqual params.chain + ''

        changeElemValue chain_textarea, angular.toJson({'the': 'json'})
        $scope.$digest()

        expect($scope.feature.params).toEqual {chain: angular.toJson({'the': 'json'})}

        changeElemValue chain_textarea, 'abc'
        $scope.$digest()

        expect($scope.feature.params).toEqual {chain: 'abc'}

      it 'should handle parameter type int and str when adding a new categorical feature', ->
        testCategorical {}

      it 'should handle parameter type int and str when editing a categorical feature', ->
        testCategorical {min_df: 321, split_pattern: 'this_pattern'}

      it 'should handle parameter type text when adding a new composite feature', ->
        testComposite {}

      it 'should handle parameter type int and str when editing a categorical feature', ->
        testComposite {chain: angular.toJson({'this': 'is json'})}

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
