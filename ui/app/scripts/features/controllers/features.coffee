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
    scaler: new Scaler({}),
    params: {}
  })

  if $routeParams.feature_id
    $scope.feature.id = $routeParams.feature_id
    $scope.feature.$load(show: Feature.MAIN_FIELDS
    ).then ((opts) ->
      #
    ), ((opts)->
      $scope.setError(opts, 'loading feature details')
    )

  params = new Parameters()
  params.$load().then ((opts)->
      $scope.configuration = opts.data.configuration
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

  $scope.$watch 'configuration', ->
    typeHasChanged()

  $scope.$watch 'feature.type', ->
    typeHasChanged()

  typeHasChanged = ->
    if not $scope.feature.type or not $scope.configuration
      return

    pType = $scope.configuration.types[$scope.feature.type]
    builtInFields = _.union(pType.required_params, pType.optional_params,
      pType.default_params)

    newParamsDict = {}
    for field in builtInFields
      # we will need to prepare the dict objects (only used in mappings),
      # otherwise leave it to the input controls
      newParamsDict[field] = if $scope.configuration.params[field].type isnt 'dict' then null else {}
    for field in _.intersection(builtInFields, _.keys($scope.feature.paramsDict))
      newParamsDict[field] = $scope.feature.paramsDict[field]

    $scope.feature.paramsDict = newParamsDict

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
