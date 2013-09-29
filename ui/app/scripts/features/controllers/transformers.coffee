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
      transformer = new Transformer()
      $scope.openDialog($dialog, transformer,
        'partials/features/transformers/add_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'add transformer',
        'transformers')

    $scope.delete = (transformer)->
      $scope.openDialog($dialog, transformer,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete predefined transformer')
])

.controller('TransformerDetailsCtrl', [
  '$scope'
  '$routeParams'
  'Transformer'

  ($scope, $routeParams, Transformer) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.transformer = new Transformer({_id: $routeParams.id})
    $scope.transformer.$load(
      show: Transformer.MAIN_FIELDS
      ).then (->), ((opts)-> $scope.setError(opts, 'loading transformer'))
  ])

.controller('AddTransformerDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'
  'Transformer'

  ($scope, $rootScope, dialog, Transformer) ->
    $scope.model = dialog.model
    $scope.dialog = dialog
    $scope.types = Transformer.$TYPES_LIST

    $scope.params = {}
    $scope.model.$getConfiguration(
    ).then ((opts)->
      $scope.configuration = opts.data.configuration
    ), ((opts)->
      $scope.setError(opts, 'loading classifier types and parameters')
    )

    $scope.loadParameters = () ->
      $scope.model.params = {}
      $scope.params = $scope.configuration[$scope.model.type]
      for name, val of $scope.params.defaults
        $scope.model.params[name] = val

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])