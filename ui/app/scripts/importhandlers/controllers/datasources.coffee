angular.module('app.importhandlers.controllers.datasources', ['app.config', ])

.controller('DataSourceChoicesLoader', [
  '$scope'
  'DataSource'

  ($scope, DataSource) ->
    $scope.types = DataSource.$TYPES_LIST
    $scope.vendors = DataSource.$VENDORS_LIST
])


.controller('DataSourcesSelectLoader', [
  '$scope'
  'DataSource'

  ($scope, DataSource) ->
    $scope.datasources = []
    DataSource.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for ds in opts.objects
        $scope.datasources.push {_id: ds._id, name: ds.name}
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading datasources')
    )
])

.controller('DataSourceListCtrl', [
  '$scope'
  '$dialog'
  'DataSource'

  ($scope, $dialog, DataSource) ->
    $scope.MODEL = DataSource
    $scope.FIELDS = DataSource.MAIN_FIELDS
    $scope.ACTION = 'loading datasources'
    $scope.LIST_MODEL_NAME = DataSource.LIST_MODEL_NAME

    $scope.edit = (ds) ->
      $scope.openDialog($dialog, ds,
        'partials/import_handler/datasource/edit.html',
        'ModelEditDialogCtrl')

    $scope.add = () ->
      ds = new DataSource()
      $scope.openDialog($dialog, ds,
        'partials/import_handler/datasource/add.html',
        'ModelEditDialogCtrl')

    $scope.delete = (ds)->
      $scope.openDialog($dialog, ds,
        'partials/base/delete_dialog.html', 'DialogCtrl')
])

.controller('DataSourceEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.handler = dialog.extra.handler
    $scope.model = dialog.extra.ds
    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
      $scope.handler.$load(
        show: 'data'
      ).then (->), (-> $scope.setError(opts, 'loading datasource details'))
    )
])