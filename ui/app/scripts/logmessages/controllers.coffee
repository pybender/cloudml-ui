'use strict'

### Log Messages specific Controllers ###

angular.module('app.logmessages.controllers', ['app.config', ])

.controller('LogMessageListCtrl', [
  '$scope'
  '$rootScope'
  'LogMessage'

($scope, $rootScope, LogMessage) ->
  $scope.init = (type, id, per_page=20) ->
    $scope.params = {'type': type, 'object_id': id,
    'sort_by': 'created_on', 'order': 'desc', 'per_page': per_page,
    'show': 'level,type,content,params,created_on'}
    $scope.log_levels = ['--any--', 'CRITICAL', 'ERROR',
                         'WARNING', 'INFO', 'DEBUG']
    $scope.log_level = '--any--'
    $scope.objects = []
    $scope.load()

  $scope.load = (concat) ->
    LogMessage.$loadAll($scope.params).then ((opts) ->
      if $scope.params['next_token']
        $scope.objects = $scope.objects.concat(opts.objects)
      else
        $scope.objects = opts.objects
      $scope.next_token = opts.next_token
    ), ((opts) ->
      $scope.setError(opts, 'loading logs')
    )

  $scope.loadMore = () ->
    $scope.params['next_token'] = $scope.next_token
    $scope.load()

  $scope.setLogLevel = () ->
    $scope.params['level'] = @log_level
    $scope.params['next_token'] = ''
    $scope.load()

  $scope.refresh = () ->
    $scope.params['next_token'] = ''
    $scope.load()
])
