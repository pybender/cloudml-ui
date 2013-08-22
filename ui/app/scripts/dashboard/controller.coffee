'use strict'

### Controllers ###

angular.module('app.dashboard.controllers', ['app.config', ])

.controller('DashboardCtrl', [
  '$scope'
  'Statistics'

  ($scope, Statistics) ->
    $scope.STYLES_MAP = {
      'New': 'info',
      'Error': 'danger',
      'Trained': 'success',
      'Completed': 'success',
      'Imported': 'success',
      'Queued': 'warning',
    }
    $scope.statistics = new Statistics()
    $scope.statistics.$load().then (->), ((opts) ->
        $scope.setError(opts, 'loading statistics'))
])