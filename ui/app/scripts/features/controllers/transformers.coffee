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

.controller('CopyFromTrainerDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'
  'Transformer'
  'Model'
  'Feature'

  ($scope, $rootScope, dialog, Transformer, Model, Feature) ->
    $scope.dialog = dialog
    $scope.model = new Transformer()

    $scope.models = []
    $scope.features = []

    $scope.loadModels = () ->
      Model.$loadAll({status: 'Trained', show: "name,features_set_id"}
      ).then ((opts) ->
        $scope.models = []
        for model in opts.objects
          $scope.models.push({
            'id': model.id,
            'name': model.name,
            'feature_set_id': model.features_set_id
          })
      ), ((opts) ->
        $scope.setError(opts, 'loading models')
      )

    $scope.loadFeatures = (modelId) ->
      model = _.find($scope.models, (m) -> m.id == modelId)
      Feature.$loadAll({
        feature_set_id: model.feature_set_id,
        transformer: '<<NOT NULL>>'
      }).then ((opts) ->
        $scope.features = []
        for feature in opts.objects
          $scope.features.push({'id': feature.id, 'name': feature.name})
      ), ((opts) ->
        $scope.setError(opts, 'loading features')
      )

    $scope.save = () ->
      $scope.model.$copyFromTrainer().then (->
        $scope.$emit 'BaseListCtrl:start:load', Transformer.LIST_MODEL_NAME
      ), ((opts) ->
        $scope.err = $scope.setError(opts, "saving")
      )
      $scope.dialog.close()

    $scope.loadModels()
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

    $scope.copyFromTrainer = () ->
      $scope.openDialog($dialog, {},
        'partials/features/transformers/copy_from_trainer.html',
        'CopyFromTrainerDialogCtrl', 'modal', 'add transformer',
        'transformers')

    $scope.delete = (transformer)->
      $scope.openDialog($dialog, transformer,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete predefined transformer')
])
