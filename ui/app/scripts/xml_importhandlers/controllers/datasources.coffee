'use strict'

angular.module(
  'app.xml_importhandlers.controllers.datasources', ['app.config', ])

.controller('DatasourcesTypesLoader', [
  '$scope'

  ($scope) ->
    $scope.types = []
    $scope.$watch('configuration', (params, old, scope) ->
        if $scope.configuration
          $scope.types = _.keys($scope.configuration)
      )
])

.controller('DatasourcesListCtrl', [
  '$scope'
  'Datasource'

  ($scope, Datasource) ->
    $scope.MODEL = Datasource
    $scope.FIELDS = Datasource.MAIN_FIELDS
    $scope.ACTION = 'loading datasources'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      # TODO: nader20140917, this watch never triggers, since the datasource
      # saved in a detached manner from the import handler, better is to listen
      # to SaveObjectCtl:save:success. and actually the BaseListCtrl
      # takes care of reloading listening to SaveObjectCtl:save:success
      $scope.$watch('handler.xml_data_sources', (datasources, old, scope) ->
        if datasources?
          $scope.objects = datasources
      )

    $scope.add = () ->
      datasource = new Datasource({
        import_handler_id: $scope.handler.id,
        params: {}
      })
      $scope.openDialog($scope, {
        model: datasource
        template: 'partials/xml_import_handlers/datasources/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'add datasource'
      })

    $scope.edit = (datasource)->
      datasource = new Datasource(datasource)
      $scope.openDialog($scope, {
        model: datasource
        template: 'partials/xml_import_handlers/datasources/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit datasource'
      })

    $scope.delete = (datasource)->
      datasource = new Datasource(datasource)
      $scope.openDialog($scope, {
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
    $scope.init = (handler_id, ds_type) ->
      $scope.handler_id = handler_id
      $scope.ds_type = ds_type
      $scope.load()

    $scope.load = () ->
      opts = {
        show: 'name'
        import_handler_id: $scope.handler_id
      }
      if $scope.ds_type
        opts.type = $scope.ds_type
      Datasource.$loadAll(opts).then ((opts) ->
        $scope.datasources = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading datasources')
      )
])
