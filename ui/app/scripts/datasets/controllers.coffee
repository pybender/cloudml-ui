'use strict'

### Dataset specific Controllers ###

angular.module('app.datasets.controllers', ['app.config', ])

.controller('DatasetListCtrl', [
  '$scope'
  '$http'
  '$dialog'
  'settings'
  'Dataset'

($scope, $http, $dialog, settings, Dataset) ->
  DataSet.$loadAll(
    $scope.handler._id,
    show: 'name,created_on,status,error,data,import_params'
  ).then ((opts) ->
    $scope.datasets = opts.objects
  ), ((opts) ->
    $scope.setError(opts, 'loading datasets')
  )
])


.controller('DatasetSelectCtrl', [
  '$scope'
  'DataSet'

  ($scope, DataSet) ->
    DataSet.$loadAll(
      $scope.handler._id,
      status: 'Imported',
      show: 'name,_id'
    ).then ((opts) ->
      $scope.datasets = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading datasets')
    )
])
