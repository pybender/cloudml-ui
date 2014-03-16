'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.scalers', ['app.config', ])

.controller('ScalersTypesLoader', [
  '$scope'
  'Scaler'

  ($scope, Scaler) ->
    $scope.types = Scaler.$TYPES_LIST
])

.controller('ScalersSelectLoader', [
  '$scope'
  'Scaler'

  ($scope, Scaler) ->
    $scope.scalers = []
    Scaler.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for sc in opts.objects
        $scope.scalers.push sc.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading scalers')
    )
])

.controller('ScalersListCtrl', [
  '$scope'
  '$dialog'
  'Scaler'

  ($scope, $dialog, Scaler) ->
    $scope.MODEL = Scaler
    $scope.FIELDS = Scaler.MAIN_FIELDS
    $scope.ACTION = 'loading scalers'
    $scope.LIST_MODEL_NAME = Scaler.LIST_MODEL_NAME

    $scope.edit = (scaler) ->
      $scope.openDialog({
        $dialog: $dialog
        model: scaler
        template: 'partials/features/scalers/edit_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit scalers'
        path: 'scalers'
      })

    $scope.add = () ->
      scalar = new Scaler()
      $scope.openDialog({
        $dialog: $dialog
        model: scalar
        template: 'partials/features/scalers/add_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'add scaler'
        path: 'scalers'
      })

    $scope.delete = (scalar) ->
      $scope.openDialog({
        $dialog: $dialog
        model: scalar
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predefined scaler'
      })
])
