'use strict'

angular.module(
  'app.xml_importhandlers.controllers.input_parameters', ['app.config', ])

# InputParameters Controllers

.controller('InputParameterTypesLoader', [
  '$scope'
  'InputParameter'

  ($scope, InputParameter) ->
    $scope.types = ["boolean","integer","float","date","string"]
    # TODO:!
    # InputParameter.$getConfiguration().then ((opts)->
    #   $scope.types = opts.configuration.types
    # ), ((opts)->
    #   $scope.setError(opts, 'loading input parameter types')
    # )
])

.controller('InputParametersListCtrl', [
  '$scope'
  '$dialog'
  'InputParameter'

  ($scope, $dialog, InputParameter) ->
    $scope.MODEL = InputParameter
    $scope.FIELDS = InputParameter.MAIN_FIELDS
    $scope.ACTION = 'loading input parameters'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.$watch('handler.xml_input_parameters', (params, old, scope) ->
        if params?
          $scope.objects = params
      )

    $scope.add = (handler) ->
      param = new InputParameter({'import_handler_id': handler.id})
      $scope.openDialog($dialog, param,
        'partials/xml_import_handlers/input_parameters/edit.html',
        'ModelEditDialogCtrl', 'modal', 'add input parameter',
        InputParameter.LIST_MODEL_NAME)

    $scope.delete = (param)->
      $scope.openDialog($dialog, param,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete input parameter')
])
