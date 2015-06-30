'use strict'

angular.module(
  'app.importhandlers.xml.controllers.input_parameters', ['app.config', ])

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
  'InputParameter'

  ($scope, InputParameter) ->
    $scope.MODEL = InputParameter
    $scope.FIELDS = InputParameter.MAIN_FIELDS
    $scope.ACTION = 'loading input parameters'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.xml_input_parameters', (params, old, scope) ->
        if params?
          $scope.objects = params
      )

    $scope.add = (handler) ->
      param = new InputParameter({'import_handler_id': handler.id})
      $scope.openDialog($scope, {
        model: param
        template: 'partials/importhandlers/xml/input_parameters/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add input parameter'
      })

    $scope.delete = (param) ->
      $scope.openDialog($scope, {
        model: param
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete input parameter'
      })
])
