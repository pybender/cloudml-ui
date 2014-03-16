'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers', ['app.config', ])

# Feature Sets specific controllers

.controller('FeaturesSetListCtrl', [
  '$scope'
  '$dialog'
  'FeaturesSet'

  ($scope, $dialog, FeaturesSet) ->
    $scope.MODEL = FeaturesSet
    $scope.FIELDS = FeaturesSet.MAIN_FIELDS
    $scope.ACTION = 'loading feature sets'

    $scope.add = () ->
      set = new FeaturesSet()
      $scope.openDialog({
        $dialog: $dialog
        model: set
        template: 'partials/features/sets/add.html'
        ctrlName: 'AddFeatureSetDialogCtrl'
        action: 'add feature set'
        list_model_name: "FeaturesSets"
      })
])

.controller('FeaturesSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  '$dialog'
  'FeaturesSet'

  ($scope, $routeParams, $dialog, FeaturesSet) ->
    # if not $routeParams.id then err = "Can't initialize without instance id"
    # $scope.featuresSet = new FeaturesSet({_id: $routeParams.id})
    $scope.init = (model) ->
      $scope.modelObj = model
      $scope.$watch('modelObj.featuresSet', (featuresSet, oldVal, scope) ->
        if featuresSet?
          $scope.featuresSet = featuresSet
          featuresSet.$load(
            show: FeaturesSet.MAIN_FIELDS
          ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

      , true)
      
    $scope.addFeature = () ->
      $scope.openDialog({
        $dialog: $dialog
        model: $scope.featuresSet
        template: 'partials/features/items/add.html'
        ctrlName: 'AddFeatureDialogCtrl'
        action: 'add feature'
        path: "feature"
      })
  ])

.controller('FeaturesListCtrl', [
  '$scope'
  '$dialog'
  'Feature'
  'NamedFeatureType'

  ($scope, $dialog, Feature, NamedFeatureType) ->
    $scope.MODEL = Feature
    $scope.FIELDS = Feature.MAIN_FIELDS
    $scope.ACTION = 'loading features'

    $scope.init = (model) ->
      $scope.modelObj = model

      # TODO: Watch only _id?
      $scope.$watch('modelObj.features_set_id', (set_id, oldVal, scope) ->
        if set_id?
          $scope.filter_opts = {'feature_set_id': set_id}
      , true)
])

# .controller('AddFeatureDialogCtrl', [
#   '$scope'
#   'dialog'
#   'Feature'
#   'NamedFeatureType'
#   'Transformer'

#   ($scope, dialog, Feature, NamedFeatureType, Transformer) ->
#     $scope.featureSet = dialog.model
#     $scope.model = new Feature({'features_set_id': $scope.featureSet._id})
#     $scope.dialog = dialog

#     $scope.$on('SaveObjectCtl:save:success', (event, current) ->
#       dialog.close()
#       $scope.$emit('BaseListCtrl:start:load', 'features')
#     )
# ])



.controller('AddFeatureTypeCtrl', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.model = new NamedFeatureType()
    $scope.types = NamedFeatureType.$TYPES_LIST
])

# .controller('FeatureTypeDetailsCtrl', [
#   '$scope'
#   '$routeParams'
#   'NamedFeatureType'
#   'Transformer'

#   ($scope, $routeParams, NamedFeatureType, Transformer) ->
#     if not $routeParams.id
#       err = "Can't initialize without id"

#     $scope.namedType = new NamedFeatureType({_id: $routeParams.id})
#     $scope.namedType.$load(
#       show: NamedFeatureType.MAIN_FIELDS
#       ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))
#   ])


.controller('FeatureActionsCtrl', [
  '$scope'
  '$dialog'
  'Transformer'
  'Scaler'

  ($scope, $dialog, Transformer, Scaler) ->
    $scope.init = (opts={}) =>
      if not opts.model
        throw new Error "Please specify feature model"

      $scope.model = opts.model

    $scope.deleteModel = (model) ->
      $scope.openDialog({
        $dialog: $dialog
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete feature'
      })

    $scope.makeRequired = (feature, is_required) ->
      feature.required = is_required
      feature.$save(only: ['required']).then (->
        $scope.$emit('updateList', [])
      ), ((opts) ->
        $scope.setError(opts, 'updating feature')
      )

    $scope.makeTarget = (feature) ->
      feature.is_target_variable = true
      feature.$save(only: ['is_target_variable']).then (->
        $scope.$emit('modelChanged', [])
        if $scope.featuresSet
          $scope.featuresSet.target_variable = feature.name
      ), ((opts) ->
        $scope.setError(opts, 'updating feature')
      )

    $scope.editScaler = (feature) ->
      $scope.openDialog({
        $dialog: $dialog
        model: null
        template: 'partials/features/scalers/edit_feature_scaler.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        extra: {'feature': feature, 'fieldname': 'scaler'}
      })

    $scope.editTransformer = (feature) ->
      $scope.openDialog({
        $dialog: $dialog
        model: null
        template: 'partials/features/transformers/edit_feature_transformer.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        extra: {'feature': feature, 'fieldname': 'transformer'}
      })

    $scope.deleteTransformer = (feature) ->
      feature.remove_transformer = true
      feature.$save(only: ['remove_transformer']).then (->
        feature.transformer = {}
      ), ((opts) ->
        $scope.setError(opts, "error while removing transformer")
      )

    $scope.deleteScaler = (feature) ->
      feature.remove_scaler = true
      feature.$save(only: ['remove_scaler']).then (->
        feature.scaler = {}
      ), ((opts) ->
        $scope.setError(opts, "error while removing scaler")
      )
])