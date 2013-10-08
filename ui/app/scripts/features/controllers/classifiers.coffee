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
      is_predefined: 1
    ).then ((opts) ->
      for tr in opts.objects
        $scope.classifiers.push tr.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading classifiers')
    )
])

.controller('ClassifiersListCtrl', [
  '$scope'
  '$dialog'
  'Classifier'

  ($scope, $dialog, Classifier) ->
    $scope.MODEL = Classifier
    $scope.FIELDS = Classifier.MAIN_FIELDS
    $scope.ACTION = 'loading classifiers'
    $scope.LIST_MODEL_NAME = Classifier.LIST_MODEL_NAME

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (classifier) ->
      $scope.openDialog($dialog, classifier,
        'partials/features/classifiers/edit_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal')

    $scope.add = () ->
      classifier = new Classifier()
      $scope.openDialog($dialog, classifier,
        'partials/features/classifiers/add_predefined.html',
        'ModelWithParamsEditDialogCtrl', 'modal', 'add transformer',
        'transformers')

    $scope.delete = (classifier)->
      $scope.openDialog($dialog, classifier,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete predefined transformer')
])

# .controller('ClassifierDetailsCtrl', [
#   '$scope'
#   '$routeParams'
#   'Classifier'

#   ($scope, $routeParams, Classifier) ->
#     if not $routeParams.id
#       err = "Can't initialize without id"

#     $scope.classifier = new Classifier({_id: $routeParams.id})
#     $scope.classifier.$load(
#       show: Classifier.MAIN_FIELDS
#       ).then (->), ((opts)-> $scope.setError(opts, 'loading classifiers'))
#   ])
