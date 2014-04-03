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
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    if dialog.model?
      $scope.model = dialog.model
    else if dialog.extra.handler? && dialog.extra.fieldname?
      $scope.handler = dialog.extra.handler
      $scope.model = eval('$scope.handler.' + dialog.extra.fieldname)

    if dialog.list_model_name?
      $scope.LIST_MODEL_NAME = dialog.list_model_name
    else
      $scope.LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME

    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

.controller('ModelCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (model) ->
      $scope.model = model
])

.controller('ModelWithParamsEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog

    if dialog.model?
      $scope.model = dialog.model
    else if dialog.extra.feature? && dialog.extra.fieldname?
      $scope.feature = dialog.extra.feature
      $scope.model = eval('$scope.feature.' + dialog.extra.fieldname)
    else if dialog.extra.model?
      $scope.target_model = dialog.extra.model
      $scope.model = eval('$scope.target_model.' + dialog.extra.fieldname)
    else
      throw new Excepion "Please spec model or feature and field name"

    if dialog.list_model_name?
      $scope.LIST_MODEL_NAME = dialog.list_model_name
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

    $scope.loadParameters = (setDefault=false) ->
      model = $scope.model
      loadParameters(model, $scope.configuration, setDefault)

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

.controller('ConfigurationLoaderCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (parentModel, fieldname) ->
      $scope.parentModel = parentModel
      $scope.fieldname = fieldname

      $scope.$watch('parentModel.' + $scope.fieldname, (model, oldVal, scope) ->
        if model?
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

    $scope.loadParameters = (setDefault=false) ->
      model = eval('$scope.parentModel.' + $scope.fieldname)
      loadParameters(model, $scope.configuration, setDefault)

])