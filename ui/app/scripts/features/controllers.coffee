'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers', ['app.config', ])

.controller('FeaturesListCtrl', [
  '$scope'
  '$location'
  'FeaturesSet'

  ($scope, $location, FeaturesSet) ->
    $scope.MODEL = FeaturesSet
    $scope.FIELDS = FeaturesSet.MAIN_FIELDS + ',tags,created_on,created_by,
updated_on,updated_by,comparable'
    $scope.ACTION = 'loading models'
    $scope.currentTag = $location.search()['tag']
    $scope.kwargs = {'tag': $scope.currentTag}
    $scope.STATUSES = ['', 'New', 'Queued', 'Importing',
    'Imported', 'Requesting Instance', 'Instance Started',
    'Training', 'Trained', 'Error', 'Canceled']
    $scope.filter_opts = {}
])


# Feature Sets specific controllers

.controller('FeaturesSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  'FeaturesSet'
  'Feature'
  'NamedFeatureType'

  ($scope, $routeParams, FeaturesSet, Feature, NamedFeatureType) ->
    if not $routeParams.id then err = "Can't initialize without instance id"
    $scope.featuresSet = new FeaturesSet({_id: $routeParams.id})

    $scope.featuresSet.$load(
      show: 'name,type,created_on,updated_on,ip,description,is_default,
  created_by'
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

    $scope.feature = new Feature()
    $scope.types = NamedFeatureType.$TYPES_LIST
    NamedFeatureType.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for nt in opts.objects
        $scope.types.push nt.name
    ), ((opts) ->
      #$scope.err = $scope.setError(opts, 'loading instances')
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

  ($scope, $routeParams, NamedFeatureType) ->
    if not $routeParams.id
      err = "Can't initialize without id"

    $scope.namedType = new NamedFeatureType({_id: $routeParams.id})
    $scope.namedType.$load(
      show: NamedFeatureType.MAIN_FIELDS
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))
  ])

.controller('FeaturesActionsCtrl', [
  '$scope'
  'FeaturesSet'

  ($scope, $rootScope, FeaturesSet) ->
    
  ])
