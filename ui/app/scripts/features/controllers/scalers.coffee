'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.scalers', ['app.config', ])

.controller('ScalersTypesLoader', [
  '$scope'
  'Scaler'

  ($scope, Scaler) ->
    $scope.types = Scaler.$TYPES_LIST
    $scope.predefined_selected = false

    # predefined scalers set the name while built-in sets the type
    $scope.$watch 'feature.scaler.name', (newVal, oldVal)->
      if not newVal
        return

      $scope.predefined_selected = true
      $scope.feature.scaler.predefined = true

    # built-in scalers set the type while the predefined sets the name
    $scope.$watch 'feature.scaler.type', (newVal, oldVal)->
      if not newVal
        return

      $scope.predefined_selected = false
      $scope.feature.scaler.predefined = false

    $scope.changeScaler = (predefined, typeOrName)->
      $scope.predefined_selected = predefined
      $scope.feature.scaler = new Scaler({})
      $scope.feature.scaler.predefined = predefined
      if predefined
        $scope.feature.scaler.name = typeOrName
      else
        $scope.feature.scaler.type = typeOrName
])

.controller('ScalersSelectLoader', [
  '$scope'
  'Scaler'

  ($scope, Scaler) ->
    $scope.scalers = []
    Scaler.$loadAll(
      show: 'name'
    ).then ((opts) ->
      $scope.predefinedScalers = []
      for sc in opts.objects
        $scope.predefinedScalers.push sc.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading predefined scalers')
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
