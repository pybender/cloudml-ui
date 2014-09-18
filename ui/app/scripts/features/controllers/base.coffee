'use strict'

### Base Feature Edit specific Controllers ###

loadParameters = (model, configuration, setDefault=false) ->
  if !model.type?
    model.params = {}
    return

  config = configuration[model.type]
  model.config = config
  if setDefault && config?
    model.params = config.defaults
  else
    model.params = model.params || {}


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

    if openOptions.list_model_name?
      $scope.LIST_MODEL_NAME = openOptions.list_model_name
    else
      $scope.LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME

    $scope.DONT_REDIRECT = true
])

# TODO: nader20140901, subject for removal cannot find any usage for it
#.controller('ModelCtrl', [
#  '$scope'
#
#  ($scope) ->
#    $scope.init = (model) ->
#      $scope.model = model
#])

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

    if openOptions.list_model_name?
      $scope.LIST_MODEL_NAME = openOptions.list_model_name
    else
      $scope.LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME

    $scope.params = {}
    $scope.model.$getConfiguration(
    ).then ((opts)->
      $scope.configuration = opts.data.configuration
      if $scope.model.type?
        $scope.loadParameters()
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

    $scope.loadParameters = () ->
      model = $scope.model
      loadParameters(model, $scope.configuration, false)
])

.controller('ConfigurationLoaderCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (parentModel, fieldname) ->
      $scope.parentModel = parentModel
      $scope.fieldname = fieldname

      $scope.$watch('parentModel.' + $scope.fieldname, (model, oldVal, scope) ->
        if model?
          $scope.configurationLoaded = false
          $scope.loadConfiguration(model)
      , true)

    $scope.loadConfiguration = (model) ->
      if $scope.configurationLoaded then return

      model.$getConfiguration(
      ).then ((opts)->
        $scope.configuration = opts.data.configuration
        $scope.configurationLoaded = true
        $scope.loadParameters()
      ), ((opts)->
        $scope.setError(opts, 'loading types and parameters')
      )

    $scope.loadParameters = ->
      model = eval('$scope.parentModel.' + $scope.fieldname)
      loadParameters(model, $scope.configuration, false)

])