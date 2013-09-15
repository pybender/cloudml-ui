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


.controller('FeaturesSetDetailsCtrl', [
  '$scope'
  '$routeParams'
  'FeaturesSet'
  'Feature'

  ($scope, $routeParams, FeaturesSet, Feature) ->
    if not $routeParams.id then err = "Can't initialize without instance id"
    $scope.featuresSet = new FeaturesSet({_id: $routeParams.id})

    $scope.featuresSet.$load(
      show: 'name,type,created_on,updated_on,ip,description,is_default,
  created_by'
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

    $scope.feature = new Feature()
    types = $scope.feature.getAvailableTypes()
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

.controller('FeatureTypeDetailsCtrl', [
  '$scope'
  '$routeParams'
  'FeaturesSet'
  'Feature'

  ($scope, $routeParams, FeaturesSet, Feature) ->
    if not $routeParams.id then err = "Can't initialize without instance id"
    $scope.featuresSet = new FeaturesSet({_id: $routeParams.id})

    $scope.featuresSet.$load(
      show: 'name,type,created_on,updated_on,ip,description,is_default,
  created_by'
      ).then (->), ((opts)-> $scope.setError(opts, 'loading featuresSet'))

    $scope.feature = new Feature()
    types = $scope.feature.getAvailableTypes()
  ])

.controller('FeaturesActionsCtrl', [
  '$scope'
  'FeaturesSet'

  ($scope, $rootScope, FeaturesSet) ->
    
  ])
