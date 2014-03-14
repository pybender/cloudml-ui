'use strict'

angular.module(
  'app.xml_importhandlers.controllers.datasources', ['app.config', ])

.controller('DatasourcesTypesLoader', [
  '$scope'
  'Datasource'

  ($scope, Datasource) ->
    $scope.types = []
    $scope.$watch('configuration', (params, old, scope) ->
        if $scope.configuration
          $scope.types = _.keys($scope.configuration)
      )
])

.controller('DatasourcesListCtrl', [
  '$scope'
  '$dialog'
  'Datasource'

  ($scope, $dialog, Datasource) ->
    $scope.MODEL = Datasource
    $scope.FIELDS = Datasource.MAIN_FIELDS
    $scope.ACTION = 'loading datasources'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.$watch('handler.datasources', (params, old, scope) ->
        if params?
          $scope.objects = params
      )

    $scope.add = () ->
      datasource = new Datasource({
        import_handler_id: $scope.handler.id,
        params: {}
      })
      $scope.openDialog($dialog, datasource,
        'partials/xml_import_handlers/datasources/edit.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'add datasource',
        Datasource.LIST_MODEL_NAME)

    $scope.edit = (datasource)->
      datasource = new Datasource(datasource)
      $scope.openDialog($dialog, datasource,
        'partials/xml_import_handlers/datasources/edit.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'edit datasource',
        Datasource.LIST_MODEL_NAME)

    $scope.delete = (datasource)->
      datasource = new Datasource(datasource)
      $scope.openDialog($dialog, datasource,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete datasource')
])
