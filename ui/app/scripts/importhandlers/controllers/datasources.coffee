angular.module('app.importhandlers.controllers.datasources', ['app.config', ])

.controller('DataSourceChoicesLoader', [
  '$scope'
  'DataSource'

  ($scope, DataSource) ->
    $scope.types = DataSource.$TYPES_LIST
    $scope.vendors = DataSource.$VENDORS_LIST
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