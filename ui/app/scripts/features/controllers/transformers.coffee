'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.transformers', ['app.config', ])

.controller('TransformersTypesLoader', [
  '$scope'
  'Transformer'

  ($scope, Transformer) ->
    $scope.types = Transformer.$TYPES_LIST
])

.controller('TransformersSelectLoader', [
  '$scope'
  'Transformer'

  ($scope, Transformer) ->
    $scope.transformers = []
    Transformer.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for tr in opts.objects
        $scope.transformers.push tr.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading transformers')
    )
])

.controller('TransformersListCtrl', [
  '$scope'
  '$modal'
  'Transformer'

  ($scope, $modal, Transformer) ->
    $scope.MODEL = Transformer
    $scope.FIELDS = Transformer.MAIN_FIELDS
    $scope.ACTION = 'loading transformers'
    $scope.LIST_MODEL_NAME = Transformer.LIST_MODEL_NAME

    $scope.edit = (transformer) ->
      $scope.openDialog({
        $modal: $modal
        model: transformer
        template: 'partials/features/transformers/edit_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit transformer'
        path: 'transformers'
      })

    $scope.add = () ->
      transformer = new Transformer()
      $scope.openDialog({
        $modal: $modal
        model: transformer
        template: 'partials/features/transformers/add_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: "add transformer"
        path: 'transformers'
      })

    $scope.delete = (transformer) ->
      $scope.openDialog({
        $modal: $modal
        model: transformer
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete transformer'
      })
])
