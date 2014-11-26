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

    expectValidity = (valid, fieldName)->

      invalid = not valid
      expect($scope.field.valid).toBe valid
      expect($scope.myForm[fieldName].$invalid).toBe invalid

    it 'should validate a required int field', ->

      createContext 'zozo',
        {type: 'int', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity false, 'theField'

      changeElemValue input, '123'
      $scope.$digest()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'

      expectValidity true, 'theField'

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expectValidity false, 'theField'

      changeElemValue input, 'xyz'
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual 'xyz'
      expectValidity false, 'theField'

    it 'should validate a not required int field', ->

      createContext 'zozo',
        {type: 'int', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity false, 'theField'

      changeElemValue input, '123'
      $scope.$digest()

      expect($scope.inputValue).toEqual '123'
      expect($scope.myForm.theField.$viewValue).toEqual '123'
      expectValidity true, 'theField'

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expectValidity true, 'theField'

      changeElemValue input, 'xyz'
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual 'xyz'
      expectValidity false, 'theField'

    it 'should validate a required str field', ->

      createContext '',
        {type: 'str', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity false, 'theField'

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expectValidity true, 'theField'

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expectValidity false, 'theField'

    it 'should validate a not required str field', ->

      createContext '',
        {type: 'str', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity true, 'theField'

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual 'abc'
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expectValidity true, 'theField'

      changeElemValue input, ''
      $scope.$digest()

      expect($scope.inputValue).toEqual ''
      expect($scope.myForm.theField.$viewValue).toEqual ''
      expectValidity true, 'theField'

    it 'should validate a required text/json field', ->

      createContext '',
        {type: 'text', required: true, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity false, 'theField'

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expectValidity false, 'theField'

      changeElemValue input, angular.toJson({some: 'json'})
      $scope.$digest()

      expect($scope.inputValue).toEqual angular.toJson({some: 'json'})
      expect($scope.myForm.theField.$viewValue).toEqual angular.toJson({some: 'json'})
      expectValidity true, 'theField'

    it 'should validate a not required text/json field', ->

      createContext '',
        {type: 'text', required: false, help_text: 'help text', valid:true}
      input = $('input', elem)

      expectValidity true, 'theField'

      changeElemValue input, 'abc'
      $scope.$digest()

      expect($scope.inputValue).toEqual undefined
      expect($scope.myForm.theField.$viewValue).toEqual 'abc'
      expectValidity false, 'theField'

      changeElemValue input, angular.toJson({some: 'json'})
      $scope.$digest()

      expect($scope.inputValue).toEqual angular.toJson({some: 'json'})
      expect($scope.myForm.theField.$viewValue).toEqual angular.toJson({some: 'json'})
      expectValidity true, 'theField'

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


    describe 'adding a new feature', ->

      it 'should handle new feature screen with no type specified', ->
        prepareContext {type: undefined, paramsDict: undefined}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.paramsDict"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
        # we are setting the paramsDict as FeatureEditCtrl would do when
        # type has been selected, the type is still undefined
        $scope.feature.paramsDict = {}
        expect ()->
          $scope.$digest()
        .not.toThrow()

    describe 'simple and complex types with switching', ->

      for type in ['text', 'float', 'numeric', 'int', 'boolean']
        do (type)->
          it "should handle simple types: #{type}", ->
            prepareContext {type: type, paramsDict: {}}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.paramsDict"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
            expect($scope.fields).toEqual []
            noParamsMsg = $('i[ng-show="fields.length <= 0"]')
            expect(noParamsMsg.length).toBe 1
            expect(noParamsMsg.hasClass('ng-hide')).toBe false
            expect($('div[class="jsonContents"]').children().length).toBe 0

      for type in [{name: 'regex', count: 1}, {name: 'map', count: 1},
        {name: 'categorical', count: 2}, {name: 'composite', count: 1},
        {name: 'categorical_label', count: 2}, {name: 'date', count: 1}]
        do (type)->
          it "should handle complex types: #{type.name}", ->
            prepareContext {type: type.name, paramsDict: {key1: undefined}}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.paramsDict"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
            expect($scope.fields.length).toBe type.count + 1
            expect(_.isEmpty(editorScope.fields)).toBe false
            noParamsMsg = $('i[ng-show="fields.length <= 0"]')
            expect(noParamsMsg.length).toBe 1
            expect(noParamsMsg.hasClass('ng-hide')).toBe true
            # The +1 in count is because of the extra field 'key1' passed in prepareContext
            # above
            expect($('div[ng-repeat="field in fields"]').length).toBe type.count + 1

      it 'should handle switching back and forth between simple and complex types', ->

        prepareContext {type: 'int', paramsDict: {}}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.paramsDict"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """

        expect($scope.fields).toEqual []
        noParamsMsg = $('i[ng-show="fields.length <= 0"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe false

        $scope.feature.type = 'categorical'
        $scope.feature.paramsDict = {min_df:undefined, split_pattern: undefined}
        $scope.$digest()

        expect($scope.fields).toEqual [
          {name: 'split_pattern', help_text : jasmine.any(String), type: 'str', required: false, valid: true, $$hashKey: jasmine.any(String) },
          {name: 'min_df', help_text : jasmine.any(String), type: 'int', required: false, valid: true, $$hashKey: jasmine.any(String) }]
        noParamsMsg = $('i[ng-show="fields.length <= 0"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe true

        $scope.feature.type = 'boolean'
        $scope.feature.paramsDict = {}
        $scope.$digest()

        expect($scope.fields).toEqual []
        noParamsMsg = $('i[ng-show="fields.length <= 0"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe false

    describe 'handling complex types with different parameter types', ->

      testCategorical = (paramsDict)->
        prepareContext {type: 'categorical', paramsDict: paramsDict}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.paramsDict"
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

        if not paramsDict.min_df
          expect(min_df_input.val()).toEqual ''
        else
          expect(min_df_input.val()).toEqual paramsDict.min_df + ''

        if not paramsDict.split_pattern
          expect(split_pattern_input.val()).toEqual ''
        else
          expect(split_pattern_input.val()).toEqual paramsDict.split_pattern

        changeElemValue min_df_input, '123'
        $scope.$digest()

        changeElemValue split_pattern_input, 'zozo'
        $scope.$digest()

        expect($scope.feature.paramsDict).toEqual {min_df: '123', split_pattern: 'zozo'}

        changeElemValue min_df_input, 'abc'
        $scope.$digest()
        expect($scope.feature.paramsDict).toEqual {min_df: undefined, split_pattern: 'zozo'}

      testComposite = (paramsDict)->
        prepareContext {type: 'composite', paramsDict: paramsDict}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.paramsDict"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """
        inputs = $('input', elem)
        textareas = $('textarea', elem)
        expect(inputs.length).toBe 0
        expect(textareas.length).toBe 1

        chain_textarea = $('textarea[name="chain"]', elem)

        expect(chain_textarea.length).toBe 1

        if not paramsDict.chain
          expect(chain_textarea.val()).toEqual ''
        else
          expect(chain_textarea.val()).toEqual paramsDict.chain

        changeElemValue chain_textarea, angular.toJson({'the': 'json'})
        $scope.$digest()

        expect($scope.feature.paramsDict).toEqual {chain: angular.toJson({'the': 'json'})}

        changeElemValue chain_textarea, 'abc'
        $scope.$digest()

        expect($scope.feature.paramsDict).toEqual {chain: undefined}

      it 'should handle parameter type int and str when adding a new categorical feature', ->
        testCategorical {min_df: undefined, split_pattern: undefined}

      it 'should handle parameter type int and str when editing a categorical feature', ->
        testCategorical {min_df: 321, split_pattern: 'this_pattern'}

      it 'should handle parameter type text when adding a new composite feature', ->
        testComposite {chain: undefined}

      it 'should handle parameter type int and str when editing a categorical feature', ->
        testComposite {chain: angular.toJson({'this': 'is json'})}

      it 'should handle type cahnges between complex types', ->
        prepareContext {type: 'categorical', paramsDict: {min_df: 321, split_pattern: 'this_pattern'}}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.paramsDict"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """

        $scope.feature.type = 'composite'
        $scope.feature.paramsDict = {chain: undefined}
        $scope.$digest()

        expect($scope.fields).toEqual [{name: 'chain', help_text : jasmine.any(String), type: 'text', required: true, valid: false, $$hashKey: jasmine.any(String) }]

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
