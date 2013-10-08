'use strict'

### Trained Model specific Controllers ###

angular.module('app.features.controllers.named_types', ['app.config', ])

.controller('NamedFeatureTypesSelectsLoader', [
  '$scope'
  'NamedFeatureType'

  ($scope, NamedFeatureType) ->
    $scope.TYPES_LIST = NamedFeatureType.$TYPES_LIST
    $scope.types = NamedFeatureType.$TYPES_LIST
    NamedFeatureType.$loadAll(show: 'name').then ((opts) ->
      for nt in opts.objects
        $scope.types.push nt.name
    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading instances')
    )
])

.controller('FeatureTypeListCtrl', [
  '$scope'
  '$dialog'
  'NamedFeatureType'

  ($scope, $dialog, NamedFeatureType) ->
    $scope.MODEL = NamedFeatureType
    $scope.FIELDS = NamedFeatureType.MAIN_FIELDS
    $scope.ACTION = 'loading named feature types'
    $scope.LIST_MODEL_NAME = NamedFeatureType.LIST_MODEL_NAME

    $scope.filter_opts = {'is_predefined': 1}

    $scope.edit = (namedType) ->
      $scope.openDialog($dialog, namedType,
        'partials/features/named_types/edit.html',
        'ModelEditDialogCtrl', 'modal')

    $scope.add = () ->
      namedType = new NamedFeatureType()
      $scope.openDialog($dialog, namedType,
        'partials/features/named_types/add.html',
        'ModelEditDialogCtrl', 'modal')

    $scope.delete = (namedType)->
      $scope.openDialog($dialog, namedType,
        'partials/base/delete_dialog.html', 'DialogCtrl', 'modal')
])
