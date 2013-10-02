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
    $scope.transformers = []
    Scaler.$loadAll(
      show: 'name'
      is_predefined: 1
    ).then ((opts) ->
      for tr in opts.objects
        $scope.transformers.push tr.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading transformers')
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

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (scalar) ->
      $scope.openDialog($dialog, scalar,
        'partials/features/scalers/edit_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'edit scalars',
        'scalars')

    $scope.add = () ->
      scalar = new Scaler()
      $scope.openDialog($dialog, scalar,
        'partials/features/scalers/add_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'add scalar',
        'scalars')

    $scope.delete = (scalar)->
      $scope.openDialog($dialog, scalar,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete predefined scalar')
])
