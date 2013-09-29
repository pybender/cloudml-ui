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
      $scope.openDialog($dialog, set,
        'partials/features/sets/add.html',
        'AddFeatureSetDialogCtrl', 'modal', 'add FeaturesSet', 'FeaturesSets')
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
      $scope.model = model
      $scope.$watch('model.featuresSet', (featuresSet, oldVal, scope) ->
        if featuresSet?
          $scope.featuresSet = featuresSet
          featuresSet.$load(
            show: FeaturesSet.MAIN_FIELDS
          ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

      , true)
      
    $scope.addFeature = () ->
      $scope.openDialog($dialog, $scope.featuresSet,
        'partials/features/items/add.html',
        'AddFeatureDialogCtrl', 'modal', 'add feature', 'feature')
  ])

.controller('AddFeatureSetDialogCtrl', [
  '$scope'
  'dialog'
  'FeaturesSet'
  'Classifier'

  ($scope, dialog, FeaturesSet, Classifier) ->
    $scope.model = dialog.model
    Classifier.$loadAll(
      show: 'name'
    ).then ((opts) ->
      $scope.classifiers = opts.objects
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading classifiers')
    )
    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

# Feature Items Controllers
.controller('FeatureFieldsSelectsLoader', [
  '$scope'
  '$dialog'
  'Transformer'
  'NamedFeatureType'

  ($scope, $dialog, Transformer, NamedFeatureType) ->
    $scope.types = NamedFeatureType.$TYPES_LIST
    NamedFeatureType.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for nt in opts.objects
        $scope.types.push nt.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading instances')
    )

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
      $scope.model = model

      $scope.$watch('model.featuresSet', (featuresSet, oldVal, scope) ->
        if featuresSet?
          $scope.filter_opts = {'features_set_id': featuresSet._id}
      , true)
      
])

.controller('AddFeatureDialogCtrl', [
  '$scope'
  'dialog'
  'Feature'
  'NamedFeatureType'
  'Transformer'

  ($scope, dialog, Feature, NamedFeatureType, Transformer) ->
    $scope.featureSet = dialog.model
    $scope.model = new Feature({'features_set_id': $scope.featureSet._id})
    $scope.dialog = dialog

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
      $scope.$emit('BaseListCtrl:start:load', 'features')
    )
])

# Classifiers Controllers

.controller('ClassifiersListCtrl', [
  '$scope'
  '$dialog'
  'Classifier'

  ($scope, $dialog, Classifier) ->
    $scope.MODEL = Classifier
    $scope.FIELDS = Classifier.MAIN_FIELDS
    $scope.ACTION = 'loading named classifiers'

    $scope.add = () ->
      classifier = new Classifier()
      $scope.openDialog($dialog, classifier,
        'partials/features/classifiers/add.html',
        'AddClassifierDialogCtrl', 'modal', 'add classifier', 'classifiers')
])

.controller('ClassifierDetailsCtrl', [
  '$scope'
  '$routeParams'
  'Classifier'

  ($scope, $routeParams, Classifier) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.classifier = new Classifier({_id: $routeParams.id})
    $scope.classifier.$load(
      show: Classifier.MAIN_FIELDS
      ).then (->), ((opts)-> $scope.setError(opts, 'loading classifiers'))
  ])

.controller('AddClassifierDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'
  'Classifier'

  ($scope, $rootScope, dialog, Classifier) ->
    $scope.model = dialog.model
    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog
    $scope.params = {}
    $scope.model.$getConfiguration(
    ).then ((opts)->
      $scope.configuration = opts.data.configuration
      if $scope.model.type?
        $scope.loadParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading classifier types and parameters')
    )

    $scope.loadParameters = (setDefault=false) ->
      $scope.params = $scope.configuration[$scope.model.type]
      if !setDefault && $scope.model.params?
        params = $scope.model.params
      else
        $scope.model.params = {}
        params = $scope.params.defaults

      for name, val of params
        $scope.model.params[name] = val

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

# Named Feature Types Controllers

# .controller('FeatureTypeListCtrl', [
#   '$scope'
#   'NamedFeatureType'

#   ($scope, NamedFeatureType) ->
#     $scope.MODEL = NamedFeatureType
#     $scope.FIELDS = NamedFeatureType.MAIN_FIELDS
#     $scope.ACTION = 'loading named feature types'
# ])


.controller('AddFeatureTypeCtrl', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.model = new NamedFeatureType()
    $scope.types = NamedFeatureType.$TYPES_LIST
])

.controller('FeatureTypeDetailsCtrl', [
  '$scope'
  '$routeParams'
  'NamedFeatureType'
  'Transformer'

  ($scope, $routeParams, NamedFeatureType, Transformer) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.namedType = new NamedFeatureType({_id: $routeParams.id})
    $scope.namedType.$load(
      show: NamedFeatureType.MAIN_FIELDS
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))
  ])


.controller('FeatureActionsCtrl', [
  '$scope'
  '$dialog'
  'Transformer'

  ($scope, $dialog, Transformer) ->
    $scope.init = (opts={}) =>
      if not opts.model
        throw new Error "Please specify feature model"

      $scope.model = opts.model

    $scope.deleteModel = (model)->
      $scope.openDialog($dialog, model,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete feature')

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
        $scope.$emit('updateList', [])
      ), ((opts) ->
        $scope.setError(opts, 'updating feature')
      )

    $scope.editTransformer = (feature) ->
      if !feature.transformer?
        feature.transformer = new Transformer({'feature_id': feature._id})

      $scope.openDialog($dialog, feature.transformer,
        'partials/features/transformers/edit_feature_transformer.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'edit feature transformer')

    $scope.deleteTransformer = (feature) ->
      alert "TODO"
])