angular.module('app.directives')

.directive('dictParameter', [ ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/dict_parameter.html'
    replace: false
    link: (scope, element, attributes, ngModel) ->
      #console.log 'in the link'

      scope.inputKeyClass = if attributes.inputKeyClass then attributes.inputKeyClass else ''
      scope.inputValueClass = if attributes.inputValueClass then attributes.inputValueClass else ''

      isEmpty = (value) ->
        if _.isString(value)
          return _.isEmpty(value.replace(/\s+/ig, ''))

        if typeof value == 'number'
          return false

        return _.isEmpty(value)

      validate = ->
        pairs = ngModel.$viewValue
        validKeys = true
        validValues = true

        for pair, index in pairs
          pair.error = {error_key: false, error_value: false, error_duplicate_key: false}
          pair.error.error_key = isEmpty(pair.key)
          pair.error.error_value = isEmpty(pair.value)
          for pair2, index2 in pairs
            if pair.key is pair2.key and index isnt index2
              pair.error.error_duplicate_key = true
              break

        validKeys = not _.some(_.pluck(_.pluck(pairs, 'error'), 'error_key'))
        validValues = not _.some(_.pluck(_.pluck(pairs, 'error'), 'error_value'))
        uniqueKeys = not _.some(_.pluck(_.pluck(pairs, 'error'), 'error_duplicate_key'))

        ngModel.$setValidity('error_keys', validKeys)
        ngModel.$setValidity('error_values', validValues)
        ngModel.$setValidity('error_no_keys', pairs.length > 0)
        ngModel.$setValidity('error_duplicate_keys', uniqueKeys)

        # adding a new key is a subset of the model being valid or not
        # the only excluded condition from validity that still allows
        # adding a new key is the model having no keys at all
        scope.canAddNewKey = validKeys and validValues and uniqueKeys

        return scope.canAddNewKey and pairs.length > 0

      scope.canAddNewKey = false
      scope.pairs = undefined

      scope.addKey = ->
        #console.log 'add key was clicked'
        pairs = _.clone(ngModel.$viewValue)
        pairs.push {key: '', value: '', error: {error_key: true, error_value: true, error_duplicate_key: false}}
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
