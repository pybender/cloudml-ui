'use strict'

### Import Handlers specific Controllers ###

angular.module('app.importhandlers.controllers', ['app.config', ])

.controller('ImportHandlerListCtrl', [
  '$scope'
  '$rootScope'
  'ImportHandler'

($scope, $rootScope, ImportHandler) ->
  $scope.MODEL = ImportHandler
  $scope.FIELDS = 'name,type,created_on,updated_on,import_params,created_by,
updated_by'
  $scope.ACTION = 'loading handler list'
])

.controller('ImportHandlerDetailsCtrl', [
  '$scope'
  '$rootScope'
  '$routeParams'
  'ImportHandler'

  ($scope, $rootScope, $routeParams, ImportHandler) ->
    if not $routeParams.id
      err = "Can't initialize without import handler id"

    $scope.handler = new ImportHandler({_id: $routeParams.id})
    $scope.LOADED_SECTIONS = []

    $scope.go = (section) ->
      name = section[0]
      if name not in $scope.LOADED_SECTIONS
        $scope.handler.$load(
          show: 'name,type,created_on,updated_on,data,import_params'
        ).then (->
          $scope.LOADED_SECTIONS.push name
        ), ((opts) ->
          $scope.setError(opts, 'loading handler details')
        )
        if name == 'dataset'
          setTimeout(() ->
            $scope.$broadcast('loadDataSet', true)
            $scope.LOADED_SECTIONS.push name
          , 100)

        

    $scope.saveData = () ->
      $scope.handler.$save(only: ['data'])
      .then (->), ((opts) ->
        $scope.setError(opts, 'saving handler details')
      )

    $scope.initSections($scope.go)
    #$scope.initLogMessages("channel=importdata_log&model=" +
    #$scope.handler._id)
])


.controller('AddImportHandlerCtl', [
  '$scope'
  'ImportHandler'

  ($scope, ImportHandler) ->
    $scope.types = [{name: 'Db'}, {name: 'Request'}]
    $scope.model = new ImportHandler()
])

.controller('DeleteImportHandlerCtrl', [
  '$scope'
  '$location'
  'dialog'
  'Model'

  ($scope, $location, dialog, Model) ->
    $scope.resetError()
    $scope.MESSAGE = dialog.action
    $scope.model = dialog.model
    $scope.path = dialog.path
    $scope.action = dialog.action
    $scope.extra_template = '/partials/import_handler/extra_delete.html'

    $scope.loadModels = () ->
      Model.$by_handler(
        handler: $scope.model._id,
        show: 'name,_id'
      ).then ((opts) ->
        $scope.umodels = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading models that use import handler')
      )

    $scope.loadModels()

    $scope.close = ->
      dialog.close()
])


.controller('ImportHandlerActionsCtrl', [
  '$scope'
  '$dialog'
($scope, $dialog) ->
  $scope.importData = (handler) ->
    $scope.openDialog($dialog, handler,
    'partials/import_handler/load_data.html', 'LoadDataDialogCtrl')

  $scope.delete = (handler) ->
    $scope.openDialog($dialog, handler,
    'partials/base/delete_dialog.html', 'DeleteImportHandlerCtrl',
    "modal", "delete import handler", "/importhandlers")

])

.controller('ImportHandlerSelectCtrl', [
  '$scope'
  'ImportHandler'

  ($scope, ImportHandler) ->
    ImportHandler.$loadAll(
      show: 'name'
    ).then ((opts) ->
      $scope.handlers = opts.objects
      $scope.handlers_list  = []
      for h in $scope.handlers
        $scope.handlers_list.push {value: h._id, text: h.name}

    ), ((opts) ->
      $scope.setError(opts, 'loading import handler list')
    )
])