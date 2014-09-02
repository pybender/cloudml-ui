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
  'Parameters'

($scope, Parameters) ->
  $scope.config = {}
  $scope.paramsConfig = {}
  $scope.requiredParams = []
  $scope.optionalParams = []

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
        required_params: [],
        optional_params: [],
      }

    $scope.config = config
    _defaults = []

    _all_params = _.union(config.required_params, config.optional_params)

    for name in _all_params
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
      _.object(_all_params, _defaults),
      _.pick($scope.model.paramsDict, _all_params)
    )
    $scope.requiredParams = config.required_params
    $scope.optionalParams = config.optional_params

  $scope.$watch('model.type', (type) ->
    $scope.loadFeatureTypeParameters()
  )
])

.controller('FeatureTypeListCtrl', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.MODEL = NamedFeatureType
    $scope.FIELDS = NamedFeatureType.MAIN_FIELDS
    $scope.ACTION = 'loading named feature types'
    $scope.LIST_MODEL_NAME = NamedFeatureType.LIST_MODEL_NAME

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (namedType) ->
      $scope.openDialog({
        model: namedType
        template: 'partials/features/named_types/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
      })

    $scope.add = () ->
      namedType = new NamedFeatureType()
      $scope.openDialog({
        model: namedType
        template: 'partials/features/named_types/add.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add new named feature type'
      })

    $scope.delete = (namedType) ->
      $scope.openDialog({
        model: namedType
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete named feature type'
      })
])
