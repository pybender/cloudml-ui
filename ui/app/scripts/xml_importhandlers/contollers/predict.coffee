'use strict'

angular.module(
  'app.xml_importhandlers.controllers.predict', ['app.config', ])

.controller('PredictCtrl', [
  '$scope'
  'XmlImportHandler'
  'PredictModel'

  ($scope, ImportHandler) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          $scope.objects = predict.models
          $scope.predict = predict
          $scope.label = predict.label
          $scope.probability = predict.probability
      )
     
])

.controller('PredictModelListCtrl', [
  '$scope'
  '$dialog'
  'PredictModel'

  ($scope, $dialog, PredictModel) ->
    $scope.MODEL = PredictModel
    $scope.FIELDS = PredictModel.MAIN_FIELDS
    $scope.ACTION = 'loading predict models'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          console.log predict
          $scope.objects = predict.models
      )

    $scope.add = ->
        model = new PredictModel({
          import_handler_id: $scope.handler.id
        })
        $scope.openDialog({
          $dialog: $dialog
          model: model
          template: 'partials/xml_import_handlers/predict/edit_model.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'add predict model'
          list_model_name: "predict_models"
        })

    $scope.delete = (model)->
      $scope.openDialog({
        $dialog: $dialog
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predict model'
        list_model_name: "predict_models"
      })
])
