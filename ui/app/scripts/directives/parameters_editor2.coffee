angular.module('app.directives')

.directive('parametersEditor2', ['$compile', '$window', ($compile, $window) ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/parameters_editor2.html'
    replace: false
    link: (scope, element, attributes, ngModel) ->
      scope.fields = []

      # The cml-model this editor is editing its parameter, either a normal
      # `Feature`, or a `NamedFeatureType`
      scope.model = scope.$eval(attributes.cmlModel)

      updateFields = ->
        if not scope.configuration or not ngModel.$modelValue or not scope.model.type
          return

        configFields = _.keys(ngModel.$modelValue)
        featureType = scope.model.type
        pType = scope.configuration.types[featureType]
        builtInFields = _.union(pType.required_params, pType.optional_params,
          pType.default_params)

        scope.fields = []
        for fieldName in _.union(builtInFields, configFields)
          field = scope.configuration.params[fieldName]
          if field
            field = _.clone(field)
            field.required = fieldName in pType.required_params
            field.name = fieldName
          else
            field = {required: false, help_text: '', type: 'str', name: fieldName}
          scope.fields.push field

      ngModel.$render = ->
        updateFields()
        scope.data = ngModel.$viewValue

      scope.$watch 'configuration', ->
        updateFields()
      return
    }
])

.directive('parameterValidator', ['$compile', ($compile) ->
    ###
      Handles validation of an input field for a feature's type parameters
      Requires $scope.field
    ###
    return {
    restrict: 'A'
    require: 'ngModel'
    priority: 10000
    link: (scope, element, attributes, ngModel) ->

      TYPE_STRING = 'str'
      TYPE_OBJECT = 'dict'
      TYPE_TEXT = 'text'
      TYPE_INT = 'int'

      _validateStrParam = (data) ->
        # string validation is any thing, unless the parameter is required
        # in which case required attribute will suffice
        data = if data then data.trim() else ''
        if scope.field.required and data is ''
          return false
        return true

      _validateJsonParam = (data) ->
        data = if data then data.trim() else ''
        if not scope.field.required and data is ''
          return true

        try
          return jQuery.parseJSON(data) isnt null
        catch e
          return false

      _validateInt = (data) ->
        data = if data then (data + '').trim() else ''
        if not scope.field.required and data is ''
          return true
        return not isNaN(parseInt(data))

      _validateObjectParam = (data) ->
        # we will only tackle the no keys validation and leave the rest
        # of validation error messages to the dictParameter directive
        return not ngModel.$error.error_no_keys

      VALIDATORS = {}
      VALIDATORS[TYPE_STRING] = _validateStrParam
      VALIDATORS[TYPE_OBJECT] = _validateObjectParam
      VALIDATORS[TYPE_TEXT] = _validateJsonParam
      VALIDATORS[TYPE_INT] = _validateInt

      attributes.$set('required', scope.field.required)

      ngModel.$parsers.push (viewValue)->
        scope.field.valid = VALIDATORS[scope.field.type](viewValue)
        ngModel.$setValidity('error', scope.field.valid)
        if not scope.field.valid
          return undefined
        else
          return viewValue

      ngModel.$formatters.push (modelValue)->
        scope.field.valid = VALIDATORS[scope.field.type](modelValue)
        ngModel.$setValidity('error', scope.field.valid)
        return modelValue
  }
])

.directive('dynamicName', ['$parse', ($parse)->
  return {
    restrict: 'A'
    priority: 10000
    controller : ['$scope', '$element', '$attrs', ($scope, $element, $attrs)->
      name = $parse($attrs.dynamicName)($scope)
      delete($attrs['dynamicName'])
      $element.removeAttr('dynamic-name')
      $attrs.$set('name', name)
    ]
  }
])