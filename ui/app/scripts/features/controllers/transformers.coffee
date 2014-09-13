'use strict'

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
      $scope.transformers = opts.objects
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

    $scope.edit = (transformer) ->
      $scope.openDialog({
        $dialog: $dialog
        model: transformer
        template: 'partials/features/transformers/edit_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit transformer'
        path: 'transformers'
      })

    $scope.add = () ->
      transformer = new Transformer()
      $scope.openDialog({
        $dialog: $dialog
        model: transformer
        template: 'partials/features/transformers/add.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: "add transformer"
        path: 'transformers'
      })

    $scope.delete = (transformer) ->
      $scope.openDialog({
        $dialog: $dialog
        model: transformer
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete transformer'
      })
])


.controller('TransformerDetailsCtrl', [
  '$scope'
  '$routeParams'
  'Transformer'
  '$location'
  '$rootScope'
  '$dialog'

($scope, $routeParams, Transformer, $location, $rootScope, $dialog) ->
  $scope.LOADED_SECTIONS = []
  if not $scope.transformer
    if not $routeParams.id
      throw new Error "Can't initialize transformer details controller
without id"

    $scope.transformer = new Transformer({
      id: $routeParams.id
    })

  $scope.load = (fields, section) ->
    $scope.transformer.$load(
      show: fields
      ).then (->
      ), ((opts)->
        $scope.setError(opts, 'loading transformer details')
      )

  $scope.LOADED_SECTIONS = []

  $scope.goSection = (section) ->
    FIELDS_BY_SECTION = {
      'training': ['error'].join(',')
      'about': [
        'type','params', 'train_import_handler',
        'field_name', 'feature_type',
        'train_import_handler_type', 'json'].join(',')
      'main': [
        'updated_on', 'created_on', 'status', 'name', 'created_by',
        'updated_by'].join(',')
    }
    name = section[0]
    subsection = section[1]
    fields = ''
    if 'main' not in $scope.LOADED_SECTIONS
      fields = FIELDS_BY_SECTION['main']
      $scope.LOADED_SECTIONS.push 'main'

    if name not in $scope.LOADED_SECTIONS
      if FIELDS_BY_SECTION[name]?
        fields += ',' + FIELDS_BY_SECTION[name]

    $scope.load(fields, name)

  $scope.initSections($scope.goSection, 'about:details')
])


.controller('TransformerActionsCtrl', [
  '$scope'
  '$dialog'
  '$rootScope'

  ($scope, $dialog, $rootScope) ->
    $scope.init = (opts) ->
      if !opts || !opts.transformer
        throw new Error "Please specify transformer"

      $scope.transformer = opts.transformer

    $scope.train = (transformer)->
      $scope._showModelActionDialog(transformer, 'train', (model) ->
        $scope.openDialog({
          $dialog: $dialog
          model: transformer
          template: 'partials/models/model_train_popup.html'
          ctrlName: 'TrainModelCtrl'
        }))

    $scope.delete = (transformer) ->
      $scope.openDialog({
        $dialog: $dialog
        model: transformer
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete transformer'
      })

    $scope._showModelActionDialog = (model, action, fn)->
      if eval('model.' + action + '_import_handler_obj')?
        fn(model)
      else
        model.$load(
          show: action + '_import_handler'
          ).then (->
            fn(model)
          ), ((opts) ->
            $scope.setError(opts, 'loading import handler details')
          )
])