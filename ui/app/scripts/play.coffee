angular.module('app.play.controllers', ['app.config', ])

.controller('PlayCtrl', [
  '$scope'
  '$timeout'

  ($scope) ->
    $scope.theDict = {}
])
