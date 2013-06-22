'use strict'

### Dataset specific Controllers ###

angular.module('app.datasets.controllers', ['app.config', ])

.controller('DatasetListCtrl', [
  '$scope'
  '$dialog'
  'DataSet'

  ($scope, $dialog, DataSet) ->
    $scope.MODEL = DataSet
    $scope.FIELDS = 'name,created_on,status,error,data,import_params,on_s3'
    $scope.ACTION = 'loading datasets'

    $scope.init = (handler) ->
      $scope.kwargs = {'handler_id': handler._id}

    $scope.delete = (dataset)->
      $scope.openDialog($dialog, dataset,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        "modal", "delete dataset", $scope.handler.objectUrl())
])

.controller('DataSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  'DataSet'

  ($scope, $routeParams, DataSet) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.dataset = new DataSet({_id: $routeParams.id,
    import_handler_id: $routeParams.handler_id})

    $scope.generateS3Url = () ->
      $scope.dataset.$generateS3Url().then ((opts) ->
        $scope.url = opts.data.url
      ), ((opts) ->
        $scope.setError(opts, 'generating url to dataset file on Amazon S3')
      )

    $scope.go = (section) ->
      $scope.dataset.$load(
        show: 'name,status,created_on,updated_on,data,on_s3,import_params,error'
      ).then (->), ((opts) ->
        $scope.setError(opts, 'loading dataset details')
      )

    $scope.initSections($scope.go, "model:details", simple=true)
])


.controller('DatasetSelectCtrl', [
  '$scope'
  'DataSet'

  ($scope, DataSet) ->
    if $scope.handler?
      DataSet.$loadAll(
        handler_id: $scope.handler._id,
        status: 'Imported',
        show: 'name,_id'
      ).then ((opts) ->
        $scope.datasets = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading datasets')
      )
])

.controller('LoadDataDialogCtrl', [
  '$scope'
  '$location'
  'dialog'
  'DataSet'

  ($scope, $location, dialog, DataSet) ->
    $scope.parameters = {}
    handler = dialog.model
    $scope.handler = handler
    $scope.params = handler.import_params

    $scope.close = ->
      dialog.close()

    $scope.start = (result) ->
      $scope.dataset = new DataSet({'import_handler_id': $scope.handler._id})
      $scope.dataset.$save($scope.parameters).then (() ->
        $scope.close()
        $location.path $scope.dataset.objectUrl()
      ), ((opts) ->
        $scope.setError(opts, 'creating dataset')
      )
])