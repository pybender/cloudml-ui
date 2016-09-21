'use strict'

### Base Feature Edit specific Controllers ###

loadParameters = (model, configuration, setDefault=false) ->
  if !model.type?
    model.params = {}
    return

  config = configuration[model.type]
  model.config = config
  if !config
    model.params = {}
    return

  if setDefault
    model.params = config.defaults || {}  # global defaults
    for field in config.parameters  # default by each field
      if field.default?
        model.params[field.name] = field.default
  else
    if config.defaults?
      model.params = _.extend config.defaults, model.params || {}
    # Checking existing parameters and deleting unexistant
    for param in model.params
      if param not in config.parameters
        delete model.params[param]

angular.module('app.features.controllers.base', ['app.config', ])

.controller('ModelEditDialogCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    if openOptions.model?
      $scope.model = openOptions.model
    else if openOptions.extra?.handler? && openOptions.extra?.fieldname?
      $scope.handler = openOptions.extra.handler
      $scope.model = eval('$scope.handler.' + openOptions.extra.fieldname)
    else
      throw new Error "Please specify a model or handler and fieldname"

    $scope.LIST_MODEL_NAME = openOptions.list_model_name || $scope.model.LIST_MODEL_NAME
    $scope.DONT_REDIRECT = true
])

.controller('ModelWithParamsEditDialogCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.DONT_REDIRECT = true

    if openOptions.model?
      $scope.model = openOptions.model
    else if openOptions.extra?.feature? && openOptions.extra?.fieldname?
      $scope.feature = openOptions.extra.feature
      $scope.model = eval('$scope.feature.' + openOptions.extra.fieldname)
    else if openOptions.extra?.model?
      $scope.target_model = openOptions.extra.model
      $scope.model = eval('$scope.target_model.' + openOptions.extra.fieldname)
    else
      throw new Error "Please specify a model or feature and field name"

    $scope.LIST_MODEL_NAME = openOptions.list_model_name || $scope.model.LIST_MODEL_NAME

    $scope.params = {}
    $scope.model.$getConfiguration(
    ).then ((opts)->
      $scope.configuration = opts.data.configuration
      $scope.configuration_list = opts.data.configuration_list
      if $scope.model.type?
        $scope.loadParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

    $scope.loadParameters = (loadDefaults=false) ->
      model = $scope.model
      loadParameters(model, $scope.configuration, loadDefaults)
])

.controller('ConfigurationLoaderCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (parentModel, fieldname) ->
      $scope.parentModel = parentModel
      $scope.fieldname = fieldname

      model = eval('$scope.parentModel.' + $scope.fieldname)
      if model?.$getConfiguration? # models having no $getConfiguration is ignored
        $scope.configurationLoaded = false
        $scope.loadConfiguration(model)

    $scope.loadConfiguration = (model) ->
      if $scope.configurationLoaded then return

      model.$getConfiguration(
      ).then ((opts)->
        $scope.configuration = opts.data.configuration
        $scope.configuration_list = opts.data.configuration_list
        $scope.configurationLoaded = true
        $scope.loadParameters(false)
      ), ((opts)->
        $scope.setError(opts, 'loading types and parameters')
      )

    $scope.loadParameters = (loadDefaults=false) ->
      model = eval('$scope.parentModel.' + $scope.fieldname)
      loadParameters(model, $scope.configuration, loadDefaults)

])