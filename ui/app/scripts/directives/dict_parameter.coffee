angular.module('app.directives')

.directive('dictParameter', ['$compile', '$window', ($compile, $window) ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/dict_parameter.html'
    replace: false
    controller: ['$scope', '$timeout', ($scope, $timeout)->
      #console.log 'in the controller'
    ]
    link: (scope, element, attributes, ngModel) ->
      #console.log 'in the link'

      isEmpty = (value)->
        if _.isString(value)
          return _.isEmpty(value.replace(/\s+/ig, ''))

        return _.isEmpty(value)

      validate = ->
        pairs = ngModel.$viewValue
        validKeys = true
        validValues = true

        for pair in pairs
          validKeys = validKeys and not isEmpty(pair.key)
          validValues = validValues and not isEmpty(pair.value)

        ngModel.$setValidity('error_keys', validKeys)
        ngModel.$setValidity('error_values', validValues)
        ngModel.$setValidity('error_no_keys', pairs.length > 0)

        scope.canAddNewKey = validKeys and validValues

        return validKeys and validValues and pairs.length > 0

      scope.canAddNewKey = false
      scope.pairs = undefined

      scope.addKey = ->
        #console.log 'add key was clicked'
        pairs = _.clone(ngModel.$viewValue)
        pairs.push {key: '', value: ''}
        # it is important to note that the $viewValue will be updated
        # from the watch on pairs
        scope.pairs = pairs

      scope.deleteKey = (index) ->
        #console.log 'delete key was clicked', index
        scope.pairs.splice index, 1

      ###
      Watching pairs is very important to update the $viewValue accordingly
      which will trigger the parsers and update the $modelValue if everything
      is ok
      ###
      scope.$watch 'pairs', (newVal, oldVal)->
        #console.log 'watching pairs', newVal, oldVal
        ngModel.$setViewValue newVal
      , true

      ngModel.$formatters.push (modelValue)->
        #console.log 'formatters was called with', modelValue
        viewValue = []
        keys = _.sortBy(_.keys(modelValue))
        for key in keys
          viewValue.push {key: key, value: modelValue[key]}

        validate()
        scope.pairs = _.clone(viewValue)
        return viewValue

      ngModel.$parsers.push (viewValue)->
        #console.log 'parsers was called with', viewValue
        if not validate()
          return undefined

        modelValue = {}
        for pair in viewValue
          modelValue[pair.key] = pair.value

        return modelValue

      return
    }
  ])
