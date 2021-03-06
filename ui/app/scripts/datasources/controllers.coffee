angular.module('app.datasources.controllers', ['app.config', ])

.controller('DataSourceFormCtrl', [
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
      show: 'name,id'
    ).then ((opts) ->
      for ds in opts.objects
        $scope.datasources.push {id: ds.id, name: ds.name}
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading datasources')
    )
])

.controller('DataSourceListCtrl', [
  '$scope'
  '$routeParams'
  'DataSource'

  ($scope, $routeParams, DataSource) ->
    $scope.MODEL = DataSource
    $scope.FIELDS = DataSource.MAIN_FIELDS
    $scope.ACTION = 'loading datasources'
    $scope.LIST_MODEL_NAME = DataSource.LIST_MODEL_NAME

    $scope.add = () ->
      ds = new DataSource({
        vendor: 'postgres'
        type: 'sql'
        conn: "host='localhost' dbname='db' user='user' password='password' port='5432'"})
      $scope.openDialog($scope, {
        model: ds
        template: 'partials/datasources/add.html'
        ctrlName: 'ModelEditDialogCtrl'
      })

    $scope.edit = (ds) ->
      $scope.openDialog($scope, {
        model: ds
        template: 'partials/datasources/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
      })
      .result
      .then ->
        return
      , ->
        $scope.$emit 'BaseListCtrl:start:load', $scope.LIST_MODEL_NAME

    $scope.delete = (ds)->
      $scope.openDialog($scope, {
        model: ds
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete datasource'
      })

    # open details dialog, when id is specified
    if $routeParams.id
      ds = new DataSource({id: $routeParams.id})
      ds.$load
        show: DataSource.MAIN_FIELDS
      .then ->
        $scope.edit(ds)
      , (opts) ->
        $scope.setError(opts, 'loading datasource details')

    # open add new datasource dialog, when action='add' spec.
    if $routeParams.action? && $routeParams.action == 'add'
      $scope.add()

])
