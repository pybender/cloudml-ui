'use strict'

### Feature specific controllers ###

angular.module('app.features.controllers.features', ['app.config', ])

# Controller for adding/edditing features fields in separate page.
# template: features/items/edit.html
.controller('FeatureEditCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Model'
  'Feature'
  'Transformer'

($scope, $routeParams, $location, Model, Feature, Transformer) ->
  if not $routeParams.model_id then throw new Error "Specify model id"
  if not $routeParams.set_id then throw new Error "Specify set id"

  $scope.modelObj = new Model({'_id': $routeParams.model_id})
  $scope.feature = new Feature({
      '_id': $routeParams.feature_id,
      'features_set_id': $routeParams.set_id,
      'transformer': {},
      'scaler': {}
  })

  if $routeParams.feature_id
    $scope.feature.$load(show: Feature.MAIN_FIELDS
    ).then (->), ((opts)-> $scope.setError(opts, 'loading feature details'))

  #  TODO: use SaveObjectCtl
  $scope.save = (fields) ->
    $scope.saving = true
    $scope.savingProgress = '0%'

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.feature.$save(only: fields).then (->
      $scope.savingProgress = '100%'
      $location.path($scope.modelObj.objectUrl())\
      .search({'action': 'features_set:list'})
    ), ((opts) ->
      $scope.err = $scope.setError(opts, "saving")
      $scope.savingProgress = '0%'
    )

  $scope.clearTransformer = () ->
    $scope.feature.transformer = {}

  $scope.clearScaler = () ->
    $scope.feature.scaler = {}
])
