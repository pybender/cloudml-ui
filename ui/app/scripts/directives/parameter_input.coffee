# Directives for edditing model's, import handler's, transformer's, scaler's parameters

angular.module('app.directives')

.directive('parameterInput', () ->
  return {
    require: 'ngModel',
    restrict: 'E',
    scope: {
      config: '='
      value: '=ngModel'
      name: '='
    }
    templateUrl:'partials/directives/parameter_input/main.html',
    link: (scope, element, attrs, ngModel) ->
      if !scope.name?
        scope.name = scope.config.name

      scope.select2Opts = null
      if scope.config.choices
        scope.select2Opts = scope.$root.getSelect2Params(
          {choices: scope.config.choices})

      scope.getFieldTemplate = (config) ->
        if config.choices
          if config.type == 'int_float_string_none'
            name = 'int_float_string_none_choices'
          else
            name = 'choices'
        else
          if config.name == 'password'
            name = 'password'
          else
            name = config.type

        return "partials/directives/parameter_input/#{name}_field.html"
  }
)

.directive('piStringListNone', () ->
  return {
    require: 'ngModel',
    restrict: 'E',
    scope: {
      config: '='
      value: '=ngModel'
      name: '='
    }
    templateUrl:'partials/directives/parameter_input/string_list_none.html',

    link: (scope, element, attrs, ngModel) ->
      scope.parameterTypes = ['string', 'list', 'empty']
      typeIsArray = Array.isArray || ( value ) -> return {}.toString.call( value ) is '[object Array]'

      typeFor = (val) ->
        res = 'empty'
        if val?
          if typeof val is 'string' then res = 'string'
          if typeIsArray val then res = 'list'
        return res

      displayFor = (val, paramType) ->
        res = val
        if paramType == 'empty' then res = null
        if val? && paramType == 'string' then res = "#{val}"
        if val? && paramType == 'list'
          if typeIsArray val
            res = val.join()
          else
            res = "#{val}"
        return res

      valueFor = (disp, paramType) ->
        if paramType == 'list'
          value = disp.split(',')
        if paramType == 'string'
          value = "#{disp}"
        if paramType == 'empty'
          value = null
        return {
          type: paramType,
          value: value
        }

      scope.parameterType = typeFor(scope.value)
      scope.displayValue = displayFor(scope.value, scope.parameterType)

      scope.change = () ->
      	scope.value = valueFor(scope.displayValue, scope.parameterType)
  }
)