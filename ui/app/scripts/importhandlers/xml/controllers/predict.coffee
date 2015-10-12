'use strict'

angular.module(
  'app.importhandlers.xml.controllers.predict', ['app.config', ])

.controller('PredictCtrl', [
  '$scope'
  'XmlImportHandler'
  'PredictLabel'
  'PredictProbability'

  ($scope, ImportHandler, PredictLabel, PredictProbability) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          $scope.objects = predict.models
          $scope.predict = predict
          if predict.label?
            predict.label.import_handler_id = handler.id
            $scope.label = new PredictLabel(predict.label)
          if predict.probability?
            predict.probability.import_handler_id = handler.id
            $scope.probability = new PredictProbability(predict.probability)
      )

    $scope.getModelsList = (models) ->
      options = []
      for model in models
        options.push({
          value: model.id,
          text: model.name
        })
      return options

    $scope.editScript = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/importhandlers/xml/predict/edit_script.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'edit script'
      })
])

.controller('PredictModelListCtrl', [
  '$scope'
  'PredictModel'
  'PredictModelWeight'

  ($scope, PredictModel, PredictModelWeight) ->
    $scope.MODEL = PredictModel
    $scope.FIELDS = PredictModel.MAIN_FIELDS + ',predict_model_weights'
    $scope.ACTION = 'loading predict models'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          $scope.objects = predict.models
      )

    $scope.add = ->
        model = new PredictModel({
          import_handler_id: $scope.handler.id
        })
        $scope.openDialog($scope, {
          model: model
          template: 'partials/importhandlers/xml/predict/edit_model.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'add predict model'
          list_model_name: "predict_models"
        })

    $scope.delete = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predict model'
        list_model_name: "predict_models"
      })

    $scope.addWeight = (model) ->
      weight = new PredictModelWeight({
          import_handler_id: $scope.handler.id,
          predict_model_id: model.id
        })
      $scope.openDialog($scope, {
        model: weight
        template: 'partials/importhandlers/xml/predict/edit_model_weight.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add predict model weight'
        list_model_name: "predict_model_weights"
      })

    $scope.editPositiveLabelScript = (model) ->
      model.editPositiveLabel = true
      $scope.openDialog($scope, {
        model: model
        template: 'partials/importhandlers/xml/predict/edit_script.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'edit script'
      })
])

.controller('PredictModelWeightListCtrl', [
  '$scope'
  'PredictModelWeight'

  ($scope, PredictModelWeight) ->
    $scope.MODEL = PredictModelWeight
    $scope.FIELDS = PredictModelWeight.MAIN_FIELDS
    $scope.ACTION = 'loading predict models weights'

    $scope.init = (predict_model) ->
      $scope.predict_model = predict_model
      $scope.kwargs = {
        import_handler_id: predict_model.import_handler_id
        predict_model_id: predict_model.id}
      if predict_model?
        $scope.objects = predict_model.predict_model_weights

    $scope.deleteWeight = (weight) ->
      $scope.openDialog($scope, {
        model: weight
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predict model weight'
        list_model_name: "predict_model_weights"
      })
])