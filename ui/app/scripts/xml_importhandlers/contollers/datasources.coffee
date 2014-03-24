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
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.xml_data_sources', (datasources, old, scope) ->
        if datasources?
          $scope.objects = datasources
      )

    $scope.add = () ->
      datasource = new Datasource({
        import_handler_id: $scope.handler.id,
        params: {}
      })
      $scope.openDialog({
        $dialog: $dialog
        model: datasource
        template: 'partials/xml_import_handlers/datasources/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'add datasource'
        #path: Datasource.LIST_MODEL_NAME
      })

    $scope.edit = (datasource)->
      $scope.openDialog({
        $dialog: $dialog
        model: datasource
        template: 'partials/xml_import_handlers/datasources/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit datasource'
        #path: Datasource.LIST_MODEL_NAME
      })

    $scope.delete = (datasource)->
      $scope.openDialog({
        $dialog: $dialog
        model: datasource
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete datasource'
      })
])


.controller('XmlDataSourceSelectCtrl', [
  '$scope'
  'Datasource'

  ($scope, Datasource) ->
    $scope.init = (handler_id) ->
      $scope.handler_id = handler_id
      $scope.load()

    $scope.load = () ->
      Datasource.$loadAll(
        show: 'name'
        import_handler_id: $scope.handler_id
      ).then ((opts) ->
        $scope.datasources = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading datasources')
      )
])
