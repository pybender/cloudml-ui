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
  'Scaler'
  'Parameters'

($scope, $routeParams, $location, Model, \
Feature, Transformer, Scaler, Parameters) ->
  if not $routeParams.model_id then throw new Error "Specify model id"
  if not $routeParams.set_id then throw new Error "Specify set id"

  $scope.modelObj = new Model({'id': $routeParams.model_id})
  $scope.feature = new Feature({
    feature_set_id: $routeParams.set_id,
    transformer: new Transformer({}),
    scaler: new Scaler({})
  })
  #$scope.config = {}
  #$scope.paramsConfig = {}
  #$scope.requiredParams = []
  #$scope.optionalParams = []

  if $routeParams.feature_id
    $scope.feature.id = $routeParams.feature_id
    $scope.feature.$load(show: Feature.MAIN_FIELDS
    ).then ((opts) ->
      #$scope.loadFeatureParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading feature details')
    )

  $scope.params = new Parameters()
  $scope.params.$load().then ((opts)->
      console.log 'loaded params configuration'
      $scope.configuration = opts.data.configuration
#      $scope.paramsConfig = $scope.configuration.params
#      $scope.loadFeatureParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

#  $scope.loadFeatureParameters = () ->
#    if not $scope.feature.type or not $scope.configuration
#      return
#
#    config = $scope.configuration.types[$scope.feature.type]
#
#    if not config
#      config = {
#        required_params: [],
#        optional_params: [],
#      }
#
#    $scope.config = config
#    _defaults = []
#
#    _all_params = _.union(config.required_params, config.optional_params)
#
#    for name in _all_params
#      type = $scope.paramsConfig[name].type
#      if type == 'dict'
#        _defaults.push({})
#      else if type == 'text'
#        _defaults.push('')
#      else
#        _defaults.push('')
#    if not $scope.feature.paramsDict
#      $scope.feature.paramsDict = {}
#    $scope.feature.paramsDict = _.extend(
#      _.object(_all_params, _defaults),
#      _.pick($scope.feature.paramsDict, _all_params)
#    )
#    $scope.requiredParams = config.required_params
#    $scope.optionalParams = config.optional_params
#
#  $scope.$watch('feature.type', (type) ->
#    $scope.loadFeatureParameters()
#  )

  #  TODO: Could we use SaveObjectCtl?
  $scope.save = (fields) ->
    # Note: We need to delete transformer or scaler when
    # transformer/scaler fields selected, when edditing
    # feature in full details page.

    is_edit = $scope.feature.id != null
    $scope.saving = true
    $scope.savingProgress = '0%'

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.feature.$save(only: fields, removeItems: true).then (->
      $scope.savingProgress = '100%'
      $location.path($scope.modelObj.objectUrl())\
      .search({'action': 'model:details'})
    ), ((opts) ->
      $scope.err = $scope.setError(opts, "saving")
      $scope.savingProgress = '0%'
    )

  $scope.clearTransformer = () ->
    $scope.feature.transformer = {}

  $scope.clearScaler = () ->
    $scope.feature.scaler = {}

  $scope.changeTransformerType = () ->
    if !$scope.feature.transformer.type
      $scope.clearTransformer()

  $scope.changePredefinedTransformer = () ->
    if not $scope.feature.transformer?.transformer
      delete $scope.feature.transformer.transformer

  $scope.changeScalerType = () ->
    if !$scope.feature.scaler.type
      $scope.clearScaler()

  $scope.changePredefinedScaler = () ->
    if not $scope.feature.scaler?.scaler
      delete $scope.feature.scaler.scaler
])
