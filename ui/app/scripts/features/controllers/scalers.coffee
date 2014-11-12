'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.scalers', ['app.config', ])

.controller('ScalersTypesLoader', [
  '$scope'
  'Scaler'

  ($scope, Scaler) ->
    is_editing = $scope.feature.id?
    $scope.types = Scaler.$TYPES_LIST
    $scope.predefined_selected = is_editing and
      not ($scope.feature.scaler.type? and
      $scope.feature.scaler.type isnt {} and
      $scope.types.indexOf($scope.feature.scaler.type) isnt -1)
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
  'Scaler'

  ($scope, Scaler) ->
    $scope.MODEL = Scaler
    $scope.FIELDS = Scaler.MAIN_FIELDS
    $scope.ACTION = 'loading scalers'
    $scope.LIST_MODEL_NAME = Scaler.LIST_MODEL_NAME

    $scope.edit = (scaler) ->
      $scope.openDialog($scope, {
        model: scaler
        template: 'partials/features/scalers/edit_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit scalers'
        path: 'scalers'
      })

    $scope.add = () ->
      scalar = new Scaler()
      $scope.openDialog($scope, {
        model: scalar
        template: 'partials/features/scalers/add_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'add scaler'
        path: 'scalers'
      })

    $scope.delete = (scalar) ->
      $scope.openDialog($scope, {
        model: scalar
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predefined scaler'
        path: scalar.BASE_UI_URL
      })
])
