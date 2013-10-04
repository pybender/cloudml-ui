'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.base', ['app.config', ])

.controller('ModelEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.model = dialog.model
    $scope.DONT_REDIRECT = true
    $scope.LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME
    $scope.dialog = dialog

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

.controller('ModelWithParamsEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.model = dialog.model
    $scope.DONT_REDIRECT = true
    $scope.LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME
    $scope.dialog = dialog
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
      $scope.params = $scope.configuration[$scope.model.type]
      if !setDefault && $scope.model.params?
        params = $scope.model.params
      else
        $scope.model.params = {}
        params = $scope.params.defaults

      for name, val of params
        $scope.model.params[name] = val

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
    )
])

.controller('ConfigurationLoaderCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (model) ->
      $scope.model = model

      $scope.model.$getConfiguration(
      ).then ((opts)->
        $scope.configuration = opts.data.configuration
        if $scope.model.type?
          $scope.loadParameters()
      ), ((opts)->
        $scope.setError(opts, 'loading types and parameters')
      )

    if $scope.model?
      $scope.init($scope.model)

    $scope.loadParameters = (setDefault=false) ->
      $scope.params = $scope.configuration[$scope.model.type]
      if !setDefault && $scope.model.params?
        params = $scope.model.params
      else
        $scope.model.params = {}
        params = $scope.params.defaults

      for name, val of params
        $scope.model.params[name] = val
])