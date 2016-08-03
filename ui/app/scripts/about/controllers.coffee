'use strict'

### Controllers ###

angular.module('app.about.controllers', ['app.config', ])

.controller('AboutCtrl', [
  '$scope'
  'About'

  ($scope, About) ->
    $scope.about = new About()
    $scope.about.$load().then (->), ((opts) ->
        $scope.setError(opts, 'loading about info'))
])