angular.module('app.directives')

.directive('listParameter', [ ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/list_parameter.html'
    replace: false
    link: (scope, element, attributes, ngModel) ->
      scope.items = []
      scope.newItem = undefined
      scope.$watch 'items', (newVal, oldVal)->
        #console.log 'watching pairs', newVal, oldVal
        ngModel.$setViewValue newVal
      , true

      scope.deleteItem = (index) ->
        #console.log 'delete key was clicked', index
        scope.items.splice index, 1

      scope.addItem = () ->
        scope.err = ''
        if scope.newItem?
          if scope.newItem in scope.items
            scope.err = 'already exist'
            return
          scope.items.push scope.newItem
          scope.newItem = undefined

      ngModel.$formatters.push (modelValue)->
        #console.log 'formatters was called with', modelValue
        viewValue = angular.fromJson(modelValue)
        # keys = _.sortBy(_.keys(modelValue))
        # for key in keys
        #   viewValue.push {key: key, value: modelValue[key]}

        # validate()

        scope.items = viewValue or []
        return viewValue
    }
  ])
