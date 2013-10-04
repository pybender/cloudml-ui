'use strict'

angular.module('app.features.controllers.features', ['app.config', ])

.controller('FeatureAddCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Model'
  'Feature'
  'Transformer'

($scope, $routeParams, $location, Model, Feature, Transformer) ->
  if not $routeParams.model_id then throw new Error "Specify model id"
  if not $routeParams.set_id then throw new Error "Specify set id"

  $scope.feature = new Feature({
    'transformer': {},
    'scaler': {},
    'features_set_id': $routeParams.set_id
  })
  $scope.modelObj = new Model({'_id': $routeParams.model_id})

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
])
