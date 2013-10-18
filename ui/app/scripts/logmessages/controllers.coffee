'use strict'

### Log Messages specific Controllers ###

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
    $scope.log_levels = ['--any--', 'CRITICAL', 'ERROR',
                         'WARNING', 'INFO', 'DEBUG']
    $scope.log_level = '--any--'

  $scope.setLogLevel = () ->
    $scope.kwargs['level'] = @log_level
    $scope.kwargs['page'] = 1
    @load()
])
