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
      $httpBackend = $injector.get('$httpBackend')
      $window = $injector.get('$window')
      $window.alert = jasmine.createSpy '$window.alert'
      $window.confirm = jasmine.createSpy('$window.confirm')

  describe 'parametersEditor', ->

    elem = null
    editorScope = null
    afterEach ->
      if elem
        elem.remove()

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
          xit "should handle simple types: #{type}", ->
            prepareContext {type: type, params: {}}, """
      <form name="myForm">
            <parameters-editor2 name="params" ng-model="feature.params"
                                parameter-type="{{feature.type}}"></parameters-editor2>
      </form>
      """
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
            expect(_.isEmpty(editorScope.fields)).toBe false
            noParamsMsg = $('i[ng-show="hasNoFields"]')
            expect(noParamsMsg.length).toBe 1
            expect(noParamsMsg.hasClass('ng-hide')).toBe true
            expect($('div[class="jsonContents"]').children().length).toBe type.count

      xit 'should handle switching back and forth between simple and complex types', ->

        prepareContext {type: 'int', params: {}}, """
  <form name="myForm">
        <parameters-editor2 name="params" ng-model="feature.params"
                            parameter-type="{{feature.type}}"></parameters-editor2>
  </form>
  """

        expect(_.isEmpty(editorScope.fields)).toBe true
        noParamsMsg = $('i[ng-show="hasNoFields"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe false

        $scope.feature.type = 'categorical'
        $scope.$digest()

        expect(_.isEmpty(editorScope.fields)).toBe false
        noParamsMsg = $('i[ng-show="hasNoFields"]')
        expect(noParamsMsg.length).toBe 1
        expect(noParamsMsg.hasClass('ng-hide')).toBe true

        $scope.feature.type = 'boolean'
        $scope.$digest()

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
