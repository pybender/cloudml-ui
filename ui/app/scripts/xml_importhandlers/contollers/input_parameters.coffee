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
      $scope.openDialog({
        $dialog: $dialog
        model: param
        template: 'partials/xml_import_handlers/input_parameters/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add input parameter'
        list_model_name: InputParameter.LIST_MODEL_NAME
      })

    $scope.delete = (param)->
      $scope.openDialog({
        $dialog: $dialog
        model: param
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete input parameter'
      })
])