'use strict'

### Dataset specific Controllers ###

angular.module('app.datasets.controllers', ['app.config', ])

.controller('DatasetListCtrl', [
  '$scope'
  '$dialog'
  'DataSet'

  ($scope, $dialog, DataSet) ->
    $scope.MODEL = DataSet
    $scope.FIELDS = 'name,created_on,status,error,data,import_params'
    $scope.ACTION = 'loading datasets'

    $scope.init = (handler) ->
      $scope.kwargs = {'handler_id': handler._id}

    $scope.delete = (dataset)->
      $scope.openDialog($dialog, dataset,
        'partials/base/delete_dialog.html', 'DeleteDialogCtrl',
        "modal", "delete dataset", $scope.handler.objectUrl())
])


.controller('DatasetSelectCtrl', [
  '$scope'
  'DataSet'

  ($scope, DataSet) ->
    if $scope.handler?
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
