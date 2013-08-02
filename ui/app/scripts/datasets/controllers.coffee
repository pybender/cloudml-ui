'use strict'

### Dataset specific Controllers ###
generateS3Url = (dataset, cb=null, errCb=null) ->
  dataset.$generateS3Url().then ((opts) ->
    cb({url: opts.data.url, dataset: dataset})
  ), ((opts) ->
    errCb(opts, 'generating Amazon S3 url')
  )

angular.module('app.datasets.controllers', ['app.config', ])

.controller('DatasetListCtrl', [
  '$scope'
  '$dialog'
  '$rootScope'
  'DataSet'

  ($scope, $dialog, $rootScope, DataSet) ->
    $scope.MODEL = DataSet
    $scope.FIELDS = 'name,created_on,status,error,data,import_params,on_s3,
filesize,records_count,time'
    $scope.ACTION = 'loading datasets'

    $scope.$on('loadDataSet', (event, opts) ->
      setTimeout(() ->
        $scope.$emit('BaseListCtrl:start:load', 'dataset')
      , 100)
    )

    $scope.$on('BaseListCtrl:load:success', (event, datasets) ->
      $scope.msg = "Please wait. Generating Amazon S3 URLs..."
      for ds in datasets
        if ds.on_s3
          generateS3Url(ds, ((opts) ->
            ds = opts.dataset
            ds.url = opts.url
            $scope.msg = "Amazon S3 URL for " + ds.data + " generated."
          ), $scope.setError)
      $scope.msg = null
    )

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

    $scope.go = (section) ->
      $scope.dataset.$load(
        show: 'name,status,created_on,updated_on,data,on_s3,import_params,error,
filesize,records_count,time'
      ).then (->
        if $scope.dataset.on_s3
          generateS3Url($scope.dataset, ((resp) ->
            $scope.url = resp.url
          ), $scope.setError)
      ), ((opts) ->
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