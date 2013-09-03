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
  '$window'

  ($scope, $dialog, $rootScope, DataSet, $window) ->
    $scope.MODEL = DataSet
    $scope.FIELDS = 'name,created_on,status,error,data,import_params,on_s3,
filesize,records_count,time,created_by,updated_by'
    $scope.ACTION = 'loading datasets'

    $scope.$on('loadDataSet', (event, opts) ->
      setTimeout(() ->
        $scope.$emit('BaseListCtrl:start:load', 'dataset')
      , 100)
    )

    $scope.init = (handler) ->
      $scope.kwargs = {'handler_id': handler._id}
])


.controller('DatasetActionsCtrl', [
  '$scope'
  '$dialog'
  '$window'
  'DataSet'

  ($scope, $dialog, $window, DataSet) ->
    $scope.init = (opts={}) =>
      if not opts.dataset
        throw new Error "Please specify dataset"

      if not opts.handler
        throw new Error "Please specify handler"

      $scope.ds = opts.dataset
      $scope.handler = opts.handler

    $scope.delete = ()->
      $scope.openDialog($dialog, $scope.ds,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        "modal", "delete dataset", $scope.handler.objectUrl())

    $scope.download = () ->
      if $scope.ds.on_s3
        generateS3Url($scope.ds, ((opts) ->
          $window.location.replace opts.url
        ), $scope.setError)

    $scope.reupload = () ->
      if $scope.ds.on_s3
        $scope.ds.$reupload()
])


.controller('DataSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  'DataSet'
  'ImportHandler'

  ($scope, $routeParams, DataSet, ImportHandler) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.dataset = new DataSet({_id: $routeParams.id,
    import_handler_id: $routeParams.handler_id})
    $scope.handler = new ImportHandler(
          {_id: $routeParams.handler_id})

    $scope.go = (section) ->
      $scope.dataset.$load(
        show: 'name,status,created_on,updated_on,data,on_s3,import_params,error,
filesize,records_count,time,created_by,import_handler_id'
      ).then (->), ((opts) ->
        $scope.setError(opts, 'loading dataset details')
      )

    $scope.initSections($scope.go, "model:details", simple=true)
])


.controller('DatasetSelectCtrl', [
  '$scope'
  'DataSet'

  ($scope, DataSet) ->
    $scope.SECTION_NAME = 'dataset'
    $scope.dataset_options = []
    $scope.activeColumns = [$scope.NEW_DATASET]

    if $scope.handler?
      DataSet.$loadAll(
        handler_id: $scope.handler._id,
        status: 'Imported',
        show: 'name,_id'
      ).then ((opts) ->
        $scope.datasets = opts.objects
        if $scope.datasets.length != 0
          $scope.activeColumns.push $scope.EXISTED_DATASET
        else
          $scope.activateColumn($scope.NEW_DATASET)

        if $scope.datasets? and not $scope.multiple_dataset
          $scope.datasets.unshift({
            _id: '',
            name: '--- select dataset ---'
          })

      ), ((opts) ->
        $scope.setError(opts, 'loading datasets')
      )

    $scope.activateColumn = (name) ->
      $scope.activateSectionColumn($scope.SECTION_NAME, name)
      $scope.currentColumn = name

    $scope.activateColumn($scope.EXISTED_DATASET)
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