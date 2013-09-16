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
    if not $routeParams.id then err = "Can't initialize without instance id"
    $scope.featuresSet = new FeaturesSet({_id: $routeParams.id})
    $scope.featuresSet.$load(
      show: FeaturesSet.MAIN_FIELDS
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

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
.controller('FeaturesListCtrl', [
  '$scope'
  '$dialog'
  'Feature'

  ($scope, $dialog, Feature) ->
    $scope.MODEL = Feature
    $scope.FIELDS = Feature.MAIN_FIELDS
    $scope.ACTION = 'loading features'

    $scope.init = (featureSet) ->
      $scope.kwargs = {'feature_set_id': featureSet._id}
])

.controller('AddFeatureDialogCtrl', [
  '$scope'
  'dialog'
  'Feature'
  'NamedFeatureType'
  'Transformer'

  ($scope, dialog, Feature, NamedFeatureType, Transformer) ->
    $scope.featureSet = dialog.model
    $scope.model = new Feature()
    $scope.dialog = dialog

    # Loads list of types
    $scope.types = NamedFeatureType.$TYPES_LIST
    NamedFeatureType.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for nt in opts.objects
        $scope.types.push nt.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading instances')
    )

    Transformer.$loadAll(
      show: 'name'
    ).then ((opts) ->
      $scope.transformers = opts.objects
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading transformers')
    )

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
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
    $scope.types = Classifier.$TYPES_LIST

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

# Transformer Controllers

.controller('TransformersListCtrl', [
  '$scope'
  '$dialog'
  'Transformer'

  ($scope, $dialog, Transformer) ->
    $scope.MODEL = Transformer
    $scope.FIELDS = Transformer.MAIN_FIELDS
    $scope.ACTION = 'loading transformers'

    $scope.add = () ->
      transformer = new Transformer()
      $scope.openDialog($dialog, transformer,
        'partials/features/transformers/add.html',
        'AddTransformerDialogCtrl', 'modal', 'add transformer', 'transformers')
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
    $scope.types = Transformer.$TYPES_LIST

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

# Named Feature Types Controllers

.controller('FeatureTypeListCtrl', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.MODEL = NamedFeatureType
    $scope.FIELDS = NamedFeatureType.MAIN_FIELDS
    $scope.ACTION = 'loading named feature types'
])


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
