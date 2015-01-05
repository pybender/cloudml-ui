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
  '$rootScope'
  'DataSet'
  '$location'

  ($scope, $rootScope, DataSet, $location) ->
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
      $scope.kwargs = {
        'import_handler_id': handler.id
        'import_handler_type': handler.TYPE}
])


.controller('DatasetActionsCtrl', [
  '$scope'
  '$window'
  'DataSet'

  ($scope, $window, DataSet) ->
    $scope.init = (opts={}) ->
      if not opts.dataset
        throw new Error "Please specify dataset"

      if not opts.handler
        throw new Error "Please specify handler"

      $scope.ds = opts.dataset
      $scope.handler = opts.handler

    $scope.delete = ()->
      $scope.openDialog($scope, {
        model: $scope.ds
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete DataSet'
        path: $scope.handler.objectUrl()
      })

    $scope.download = () ->
      if $scope.ds.on_s3
        generateS3Url($scope.ds, ((opts) ->
          $window.location.replace(opts.url)
        ), $scope.setError)

    $scope.reupload = () ->
      if !$scope.ds.on_s3
        $scope.ds.$reupload()

    $scope.reimport = () ->
      $scope.ds.$reimport()

    $scope.getPigFields = (dataSet)->
      $scope.openDialog($scope, {
        model: dataSet
        template: 'partials/xml_import_handlers/sqoop/load_pig_fields.html'
        ctrlName: 'PigFieldsLoader'
      })
])


.controller('DataSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'DataSet'
  'ImportHandler'
  'XmlImportHandler'

  ($scope, $routeParams, $location, DataSet, ImportHandler, XmlImportHandler) ->
    if not $routeParams.id
      throw new Error "Can't initialize without id"

    if not $routeParams.import_handler_type
      throw new Error "Can't initialize without import_handler_type"

    if not $routeParams.import_handler_id
      throw new Error "Can't initialize without import_handler_id"

    if $routeParams.import_handler_type == 'xml'
      cls = XmlImportHandler
    else
      cls = ImportHandler

    $scope.handler = new cls({
      id: $routeParams.import_handler_id
    })

    $scope.dataset = new DataSet({
      id: $routeParams.id
      import_handler: $scope.handler
    })

    $scope.go = (section) ->
      $scope.dataset.$load
        show: DataSet.MAIN_FIELDS + ',' + DataSet.EXTRA_FIELDS
      .then ->
        if $scope.dataset.status and
            $scope.dataset.status is DataSet.STATUS_IMPORTED
          $scope.dataset.$getSampleData()
          .then (resp)->
            $scope.dataset.samples_json = angular.toJson(resp.data, true)
          , (opts)->
            $scope.setError(opts, 'error loading dataset sample data')
      , (opts) ->
        $scope.setError(opts, 'loading dataset details')

    $scope.initSections($scope.go, "model:details", simple=true)
    $scope.host = $location.host()

    # TODO: make it global
    $scope.getCssClassByStatus = (opts) ->
      status = opts.status
      MAP = {'Terminated': 'badge-inverse', 'Error': 'badge-important'}
      if status? && MAP[status]?
        return MAP[status]
      return opts.default or 'badge-info'
])


.controller('DatasetSelectCtrl', [
  '$scope'
  'DataSet'

  ($scope, DataSet) ->
    $scope.init = (handler) ->
      if handler?
        $scope.handler = handler
        $scope.load()
      else
        throw Error('Specify import handler')

    $scope.load = ->
      DataSet.$loadAll({
        import_handler_id: $scope.handler.id,
        import_handler_type: $scope.handler.TYPE,
        status: 'Imported',
        show: 'name'
      }).then ((opts) ->
        $scope.datasets = opts.objects
        if $scope.data? && $scope.datasets? && $scope.datasets.length == 0
          $scope.data.new_dataset_selected = 1

        if $scope.datasets? and not $scope.multiple_dataset
          $scope.datasets.unshift({
            id: '',
            name: '--- select dataset ---'
          })

      ), ((opts) ->
        $scope.setError(opts, 'loading datasets')
      )
])

.controller('LoadDataDialogCtrl', [
  '$scope'
  '$location'
  'openOptions'
  'DataSet'

  ($scope, $location, openOptions, DataSet) ->
    $scope.parameters = {}
    handler = openOptions.model
    $scope.handler = handler
    # TODO: nader20140917, json IH has the tendency of accepting duplicate
    # parameters which affects the repeater in load_data.html and also affects
    # the number of fields in the dataset import dialog bog
    $scope.params = _.uniq(handler.import_params)
    $scope.format = 'json'
    $scope.formats = [
      {name: 'JSON', value: 'json'}, {name: 'CSV', value: 'csv'}
    ]

    $scope.start = (result) ->
      $scope.dataset = new DataSet({
        'import_handler_id': $scope.handler.id
        'import_handler_type': $scope.handler.TYPE
      })
      data = {
        import_params: JSON.stringify($scope.parameters),
        format: $scope.format
        handler_type: $scope.handler.TYPE
      }
      $scope.dataset.$save(data)
      .then ->
        $scope.$close(true)
        $location.url $scope.dataset.objectUrl()
      , (opts) ->
        $scope.setError(opts, 'creating dataset')
])