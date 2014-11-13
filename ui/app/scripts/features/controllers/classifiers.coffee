'use strict'

angular.module('app.features.controllers.classifiers', ['app.config', ])

# Classifiers Controllers

.controller('ClassifierTypesLoader', [
  '$scope'
  'Classifier'

  ($scope, Classifier) ->
    $scope.types = Classifier.$TYPES_LIST
])

.controller('ClassifiersSelectLoader', [
  '$scope'
  'Classifier'

  ($scope, Classifier) ->
    $scope.classifiers = []
    Classifier.$loadAll(
      show: 'name'
    ).then ((opts) ->
      for classifier in opts.objects
        $scope.classifiers.push {id: classifier.id, name: classifier.name}
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading classifiers')
    )
])

.controller('ClassifiersListCtrl', [
  '$scope'
  'Classifier'

  ($scope, Classifier) ->
    $scope.MODEL = Classifier
    $scope.FIELDS = Classifier.MAIN_FIELDS
    $scope.ACTION = 'loading classifiers'
    $scope.LIST_MODEL_NAME = Classifier.LIST_MODEL_NAME

    $scope.edit = (classifier) ->
      $scope.openDialog($scope, {
        model: classifier
        template: 'partials/features/classifiers/edit_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
      })

    $scope.add = () ->
      classifier = new Classifier()
      $scope.openDialog($scope, {
        model: classifier
        template: 'partials/features/classifiers/add_predefined.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'add classifier'
        path: "classifiers"
      })

    $scope.delete = (classifier) ->
      $scope.openDialog($scope, {
        model: classifier
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete predefined classifier'
        path: classifier.BASE_UI_URL
      })
])
