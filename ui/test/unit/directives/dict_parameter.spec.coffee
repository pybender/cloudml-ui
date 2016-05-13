'use strict'

# jasmine specs for directives go here
describe "directives/parametersEditor", ->

  $compile = null
  $rootScope = null
  $scope = null

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

    module 'app.base'
    module "app.directives"
    module 'app.templates' # to serve partials html

    inject ($injector) ->
      $rootScope = $injector.get('$rootScope')
      $compile = $injector.get('$compile')

  describe 'dictParameter', ->

    prepareContext = (theDict) ->
      $scope = $rootScope.$new()
      $scope.theDict = theDict

      html = """
<form name="myForm">
  <dict-parameter ng-model="theDict" name="model"></dict-parameter>
</form>
        """

      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()

    it 'should trigger 3 errors based on the modelValue, and disable/enable the add button', ->

      prepareContext {}
      expect($scope.myForm.model.$error).toEqual {error_keys: false, error_values: false, error_no_keys: true, error_duplicate_keys: false, regexp_key_error: false, regexp_val_error: false}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      expect($scope.theDict).toBeUndefined()

      $scope.theDict = {'': 'zozo'}
      $scope.$digest()
      expect($scope.myForm.model.$error).toEqual {error_keys: true, error_values: false, error_no_keys: false, error_duplicate_keys: false, regexp_key_error: true, regexp_val_error: false}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()

      $scope.theDict = {'zinger': ''}
      $scope.$digest()
      expect($scope.myForm.model.$error).toEqual {error_keys: false, error_values: true, error_no_keys: false, error_duplicate_keys: false, regexp_key_error: false, regexp_val_error: true}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()

      $scope.theDict = {'': ''}
      $scope.$digest()
      expect($scope.myForm.model.$error).toEqual {error_keys: true, error_values: true, error_no_keys: false, error_duplicate_keys: false, regexp_key_error: true, regexp_val_error: true}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()

    it 'should manage the state of add button after addition and deletion', ->
      prepareContext {}

      # make sure we are on the right state
      expect($scope.myForm.model.$error).toEqual {error_keys: false, error_values: false, error_no_keys: true, error_duplicate_keys: false, regexp_key_error: false, regexp_val_error: false}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      $('button[ng-click="addKey()"]').click()
      $scope.$digest()

      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()
      expect($scope.myForm.model.$viewValue).toEqual [{key: '', value: '', $$hashKey: jasmine.any(String),
      error: {error_key: true, error_value: true, error_duplicate_key: false, regexp_key_error: true, regexp_val_error: true }}]

      # fill in the values and the add button will get enabled
      changeElemValue $('input[ng-model="pair.key"]'), 'the_key'
      changeElemValue $('input[ng-model="pair.value"]'), 'the_value'
      $scope.$digest()

      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      expect($scope.myForm.model.$viewValue).toEqual [{key: 'the_key', value: 'the_value', $$hashKey: jasmine.any(String)
      error: { error_key: false, error_value: false, error_duplicate_key : false, regexp_key_error: false, regexp_val_error: false }}]
      expect($scope.theDict).toEqual {the_key: 'the_value'}

      # click the add button a new row will be added and the add button will be disabled
      $('button[ng-click="addKey()"]').click()
      $scope.$digest()
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()
      expect($scope.myForm.model.$viewValue).toEqual [
        {key: 'the_key', value: 'the_value', error: {error_key: false, error_value: false, error_duplicate_key: false, regexp_key_error: false, regexp_val_error: false }, $$hashKey: jasmine.any(String)}
        {key: '', value: '', error: {error_key : true, error_value: true, error_duplicate_key: false, regexp_key_error: true, regexp_val_error: true }, $$hashKey: jasmine.any(String)}
      ]

      # click the remove button on the new row and everything will be ok
      $('button[ng-click="deleteKey($index)"]:last').click()
      $scope.$digest()
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      expect($scope.myForm.model.$viewValue).toEqual [{key: 'the_key', value: 'the_value', $$hashKey: jasmine.any(String)
      error: {error_key : false, error_value: false, error_duplicate_key: false, regexp_key_error: false, regexp_val_error: false }}]
      expect($scope.theDict).toEqual {the_key: 'the_value'}

      # add & fill again and everythign will be ok
      $('button[ng-click="addKey()"]').click()
      $scope.$digest()
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()
      expect($scope.myForm.model.$viewValue).toEqual [
        {key: 'the_key', value: 'the_value', error: {error_key : false, error_value: false, error_duplicate_key: false, regexp_key_error: false, regexp_val_error: false }, $$hashKey: jasmine.any(String)}
        {key: '', value: '', error: {error_key : true, error_value: true, error_duplicate_key: false, regexp_key_error: true, regexp_val_error: true }, $$hashKey: jasmine.any(String)}
      ]

      ngRepeatDiv = $('div[ng-repeat="pair in pairs"]:last')
      changeElemValue $('input[ng-model="pair.key"]', ngRepeatDiv), 'the_key2'
      changeElemValue $('input[ng-model="pair.value"]', ngRepeatDiv), 'the_value2'
      $scope.$digest()
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      expect($scope.myForm.model.$viewValue).toEqual [
        {key: 'the_key', value: 'the_value', error: {error_key : false, error_value: false, error_duplicate_key: false, regexp_key_error: false, regexp_val_error: false }, $$hashKey: jasmine.any(String)}
        {key: 'the_key2', value: 'the_value2', error: {error_key : false, error_value: false, error_duplicate_key: false, regexp_key_error: false, regexp_val_error: false }, $$hashKey: jasmine.any(String)}
      ]
      expect($scope.theDict).toEqual {the_key: 'the_value', the_key2: 'the_value2'}

    it 'should be invalid when adding 2 keys of the same key name', ->
      prepareContext {the_key: 'the_value'}
      $('button[ng-click="addKey()"]').click()
      $scope.$digest()

      ngRepeatDiv = $('div[ng-repeat="pair in pairs"]:last')
      changeElemValue $('input[ng-model="pair.key"]', ngRepeatDiv), 'the_key'
      changeElemValue $('input[ng-model="pair.value"]', ngRepeatDiv), 'the_value2'
      $scope.$digest()
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe false
      expect($scope.theDict).toBeUndefined()
      expect($scope.myForm.model.$viewValue).toEqual [
        {key: 'the_key', value: 'the_value', error: {error_key : false, error_value: false, error_duplicate_key: true, regexp_key_error: false, regexp_val_error: false}, $$hashKey: jasmine.any(String)}
        {key: 'the_key', value: 'the_value2', error: {error_key : false, error_value: false, error_duplicate_key: true, regexp_key_error: false, regexp_val_error: false}, $$hashKey: jasmine.any(String)}
      ]
      expect($scope.myForm.model.$error).toEqual {error_keys: false, error_values: false, error_no_keys: false, error_duplicate_keys: true, regexp_key_error: false, regexp_val_error: false}

  describe 'dictParameter with parameterValidator', ->

    prepareContext = (theDict) ->
      $scope = $rootScope.$new()
      $scope.theDict = theDict
      $scope.field = {type: 'dict'}

      html = """
<form name="myForm">
  <dict-parameter ng-model="theDict" name="model" parameter-validator=""></dict-parameter>
</form>
        """

      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()

    it 'should allow parameterValidator to intervene without disrupting the modelVale of the dictionary', ->
      prepareContext {}

      expect($scope.myForm.model.$error).toEqual {error : true, error_keys: false, error_values: false, error_no_keys: true, error_duplicate_keys: false, regexp_key_error: false, regexp_val_error: false}
      expect($('button[ng-click="addKey()"]').is(':enabled')).toBe true
      $('button[ng-click="addKey()"]').click()
      $scope.$digest()

      ngRepeatDiv = $('div[ng-repeat="pair in pairs"]:last')
      changeElemValue $('input[ng-model="pair.key"]', ngRepeatDiv), 'the_key'
      changeElemValue $('input[ng-model="pair.value"]', ngRepeatDiv), 'the_value'
      $scope.$digest()

      expect($scope.myForm.model.$viewValue).toEqual [{key: 'the_key', value: 'the_value', $$hashKey: jasmine.any(String)
      error: { error_key: false, error_value: false, error_duplicate_key : false, regexp_key_error: false, regexp_val_error: false }}]
      expect($scope.theDict).toEqual {the_key: 'the_value'}


