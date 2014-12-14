'use strict'

angular.module('app.features.controllers.transformers', ['app.config', ])

.controller('TransformersTypesLoader', [
  '$scope'
  'Transformer'

  ($scope, Transformer) ->
    $scope.types = Transformer.$TYPES_LIST
    $scope.predefined_selected = false

    $scope.$watch 'feature.transformer', (newVal, oldVal)->
      if not newVal
        return

      $scope.predefined_selected = newVal.id > 0

    $scope.changeTransformer = (id, type)->
      $scope.feature.transformer = new Transformer({id: id, type: type})
])

.controller('TransformersSelectLoader', [
  '$scope'
  'Transformer'

  ($scope, Transformer) ->
    $scope.transformers = []
    Transformer.$loadAll(
      show: 'name'
      status: 'Trained'
    ).then ((opts) ->
      $scope.pretrainedTransformers = opts.objects
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading pretrained transformers')
    )

    $scope.pretrainedIdToType = (id)->
      return _.filter($scope.pretrainedTransformers, { id: id })[0].name
  ])

.controller('TransformersListCtrl', [
  '$scope'
  'Transformer'

  ($scope, Transformer) ->
    $scope.MODEL = Transformer
    $scope.FIELDS = Transformer.MAIN_FIELDS
    $scope.ACTION = 'loading transformers'
    $scope.LIST_MODEL_NAME = Transformer.LIST_MODEL_NAME

    $scope.add = () ->
      transformer = new Transformer()
      $scope.openDialog($scope, {
        model: transformer
        template: 'partials/features/transformers/add.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: "add transformer"
        path: 'transformers'
      })
])

.controller('TransformerDetailsCtrl', [
  '$scope'
  '$routeParams'
  'Transformer'
  '$location'
  '$rootScope'

($scope, $routeParams, Transformer) ->
  $scope.LOADED_SECTIONS = []
  if not $scope.transformer
    if not $routeParams.id
      throw new Error "Can't initialize transformer details controller without id"

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
      'training': [
        'error', 'memory_usage', 'trainer_size', 'training_time',
        'trained_by'
      ].join(',')
      'about': [
        'type','params', 'field_name', 'feature_type', 'json'].join(',')
      'main': [
        'updated_on', 'created_on', 'status', 'name',
        'created_by', 'updated_by',
        'train_import_handler_type', 'train_import_handler'].join(',')
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
      $scope.LOADED_SECTIONS.push name

    if fields isnt '' # otherwise we had those loaded before
      $scope.load(fields, name)

  $scope.initSections($scope.goSection, 'about:details')
])


.controller('TransformerActionsCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (opts) ->
      if !opts || !opts.transformer
        throw new Error "Please specify transformer"

      $scope.transformer = opts.transformer

    $scope.train = (transformer) ->
      transformer.$load(
        show: 'train_import_handler,train_import_handler_type'
      ).then (->
        $scope.openDialog($scope, {
          model: transformer
          template: 'partials/models/model_train_popup.html'
          ctrlName: 'TrainModelCtrl'
        })
      ), ((opts) ->
        $scope.setError(opts, 'loading import handler details')
      )

    $scope.changeType = (transformer) ->
      $scope.openDialog($scope, {
        model: transformer
        template: 'partials/features/transformers/edit_type.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
      })

    $scope.delete = (transformer) ->
      $scope.openDialog($scope, {
        model: transformer
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete transformer'
        path: transformer.BASE_UI_URL
      })
])
