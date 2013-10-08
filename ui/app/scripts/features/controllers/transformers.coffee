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
      is_predefined: 1
    ).then ((opts) ->
      for tr in opts.objects
        $scope.transformers.push tr.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading transformers')
    )
])

.controller('TransformersListCtrl', [
  '$scope'
  '$dialog'
  'Transformer'

  ($scope, $dialog, Transformer) ->
    $scope.MODEL = Transformer
    $scope.FIELDS = Transformer.MAIN_FIELDS
    $scope.ACTION = 'loading transformers'
    $scope.LIST_MODEL_NAME = Transformer.LIST_MODEL_NAME

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (transformer) ->
      $scope.openDialog($dialog, transformer,
        'partials/features/transformers/edit_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'edit transformer',
        'transformers')

    $scope.add = () ->
      transformer = new Transformer({'is_predefined': true})
      $scope.openDialog($dialog, transformer,
        'partials/features/transformers/add_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'add transformer',
        'transformers')

    $scope.delete = (transformer)->
      $scope.openDialog($dialog, transformer,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete predefined transformer')
])
