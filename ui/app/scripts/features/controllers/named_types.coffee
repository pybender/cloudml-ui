'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.named_types', ['app.config', ])

.controller('NamedFeatureTypesSelectsLoader', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.TYPES_LIST = NamedFeatureType.$TYPES_LIST
    NamedFeatureType.$loadAll(show: 'name').then ((opts) ->
      predefined = (t.name for t in opts.objects)
      $scope.types = NamedFeatureType.$TYPES_LIST.concat predefined
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading instances')
    )
])

# Controller for adding/edditing feature types with dialog.
.controller('FeatureTypeEditCtrl', [
  '$scope'
  '$routeParams'
  '$filter'
  '$location'
  'NamedFeatureType'
  'Parameters'

($scope, $routeParams, $filter, $location, NamedFeatureType, Parameters) ->
  $scope.config = {}
  $scope.paramsConfig = {}
  $scope.requiredParams = []

  $scope.params = new Parameters()
  $scope.params.$load().then ((opts)->
      $scope.configuration = opts.data.configuration
      $scope.paramsConfig = $scope.configuration.params
      $scope.loadFeatureTypeParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

  $scope.loadFeatureTypeParameters = () ->
    if !$scope.model.type || !$scope.configuration
      return

    config = $scope.configuration.types[$scope.model.type]

    if not config
      config = {
        required_params: []
      }

    $scope.config = config
    _defaults = []

    for name in config.required_params
      type = $scope.paramsConfig[name].type
      if type == 'dict'
        _defaults.push({})
      else if type == 'text'
        _defaults.push('')
      else
        _defaults.push('')
    if not $scope.model.paramsDict
      $scope.model.paramsDict = {}
    $scope.model.paramsDict = _.extend(
      _.object(config.required_params, _defaults),
      _.pick($scope.model.paramsDict, config.required_params)
    )
    $scope.requiredParams = config.required_params

  $scope.$watch('model.type', (type) ->
    $scope.loadFeatureTypeParameters()
  )
])

.controller('FeatureTypeListCtrl', [
  '$scope'
  '$dialog'
  'NamedFeatureType'

  ($scope, $dialog, NamedFeatureType) ->
    $scope.MODEL = NamedFeatureType
    $scope.FIELDS = NamedFeatureType.MAIN_FIELDS
    $scope.ACTION = 'loading named feature types'
    $scope.LIST_MODEL_NAME = NamedFeatureType.LIST_MODEL_NAME

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (namedType) ->
      $scope.openDialog($dialog, namedType,
        'partials/features/named_types/edit.html',
        'ModelEditDialogCtrl', 'modal')

    $scope.add = () ->
      namedType = new NamedFeatureType()
      $scope.openDialog($dialog, namedType,
        'partials/features/named_types/add.html',
        'ModelEditDialogCtrl', 'modal')

    $scope.delete = (namedType)->
      $scope.openDialog($dialog, namedType,
        'partials/base/delete_dialog.html', 'DialogCtrl', 'modal')
])
