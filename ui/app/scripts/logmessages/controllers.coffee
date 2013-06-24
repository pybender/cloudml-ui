'use strict'

### Import Handlers specific Controllers ###

angular.module('app.logmessages.controllers', ['app.config', ])

.controller('LogMessageListCtrl', [
  '$scope'
  '$rootScope'
  'LogMessage'

($scope, $rootScope, LogMessage) ->
  $scope.MODEL = LogMessage
  $scope.FIELDS = 'level,type,content,params,created_on'
  $scope.ACTION = 'loading logs'

  $scope.init = (type, _id) ->
    $scope.kwargs = {'type': type, 'params.obj': _id, 'page': 1,
    'sort_by': 'created_on', 'order': 'desc'}
])