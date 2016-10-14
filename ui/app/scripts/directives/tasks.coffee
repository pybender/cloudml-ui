angular.module('app.directives')

.directive('tasks', [ ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/tasks.html'
    replace: false
    scope: {
      value: '=ngModel'
      taskConfig: '='
      taskTypes: '='
    }
    link: ($scope, element, attributes, ngModel) ->
      $scope.scenario = {}
      $scope.scenario.callback_kwargs = {}
      $scope.scenario.tasks = []
      $scope.kwargs = {}

      $scope.setScenario = () ->
        if $scope.scenario.type == 'single'
          $scope.scenario['tasks'] = [$scope.task.task]
          $scope.scenario['kwargs'] = $scope.kwargs || {}
        else
          if $scope.scenario.type == 'chord'
            $scope.scenario.callback = $scope.scenario.callback.task
            $scope.scenario.callback_kwargs = $scope.scenario.callback_kwargs || {}
        $scope.value = angular.toJson($scope.scenario)
        $scope.value = $scope.scenario
        console.log $scope.scenario
        console.log $scope.value

      $scope.resetScenario = () ->
        $scope.scenario.tasks = []
        $scope.scenario.kwargs = {}
        $scope.scenario.callback = undefined
        $scope.scenario.callback_kwargs = {}
        $scope.task = undefined
        $scope.kwargs = {}

      $scope.addChainedTask = () ->
        $scope.scenario.tasks.push {
            tasks: [$scope.task.task],
            kwargs: $scope.kwargs || {},
            type: 'single'
        }
        $scope.task = undefined
        $scope.kwargs = {}

      $scope.$watch 'scenario.type', (nVal, oVal) ->
        if nVal != oVal && oVal != undefined
          $scope.resetScenario()

      $scope.delChainedTask = (t) ->
        $scope.scenario.tasks.splice(t, 1)

  }
])
