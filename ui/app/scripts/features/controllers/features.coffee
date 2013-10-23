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
  '$filter'

($scope, $routeParams, $location, Model, Feature, Transformer, $filter) ->
  if not $routeParams.model_id then throw new Error "Specify model id"
  if not $routeParams.set_id then throw new Error "Specify set id"

  $scope.modelObj = new Model({'_id': $routeParams.model_id})
  $scope.feature = new Feature({
    features_set_id: $routeParams.set_id,
    transformer: {},
    scaler: {}
  })
  $scope.config = {}
  $scope.feature_params = {}
  $scope.params_config = {}
  $scope.required_params = []

  if $routeParams.feature_id
    $scope.feature._id = $routeParams.feature_id
    $scope.feature.$load(show: Feature.MAIN_FIELDS
    ).then ((opts) ->
      $scope.loadFeatureParameters()),
      ((opts)-> $scope.setError(opts, 'loading feature details'))

  $scope.feature.$getConfiguration().then ((opts)->
      $scope.configuration = opts.data.configuration
      $scope.params_config = $scope.configuration.params
      $scope.loadFeatureParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

  $scope.loadFeatureParameters = () ->
    if !$scope.feature.type || !$scope.configuration
      return

    config = $scope.configuration.types[$scope.feature.type]

    if not config
      config = {
        required_params: []
      }

    $scope.config = config
    _defaults = []
    for name in config.required_params
      type = $scope.params_config[name].type
      if type == 'dict'
        _defaults.push({})
      else if type == 'list'
        _defaults.push([])
      else
        _defaults.push('')
#    $scope.feature.params = _.object(config.required_params, _defaults)
    $scope.feature.params = _.extend(
      _.object(config.required_params, _defaults),
      _.pick($scope.feature.params, config.required_params)
    )
    $scope.required_params = config.required_params
    $scope.feature_params = _.clone($scope.feature.params)

  $scope.$watch('feature.type', (type) ->
    $scope.loadFeatureParameters()
  )

  #  TODO: Could we use SaveObjectCtl?
  $scope.save = (fields) ->
    # Note: We need to delete transformer or scaler when
    # transformer/scaler fields selected, when edditing
    # feature in full details page.

    # Save parameters
    # TODO: clean JSON inside the control
    $scope.feature.params = JSON.parse($filter('json')($scope.feature_params))

    is_edit = $scope.feature._id != null
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

  $scope.changeScalerType = () ->
    if !$scope.feature.scaler.type
      $scope.clearScaler()
])
