'use strict'

### Dataset specific Controllers ###

angular.module('app.datasets.controllers', ['app.config', ])

.controller('DatasetListCtrl', [
  '$scope'
  '$http'
  '$dialog'
  'settings'
  'Dataset'

($scope, $http, $dialog, settings, Dataset) ->
  Dataset.$loadAll(
    show: 'name,created_on,updated_on'
  ).then ((opts) ->
    $scope.objects = opts.objects
  ), ((opts) ->
    $scope.err = "Error while saving: server responded with " +
        "#{resp.status} " +
        "(#{resp.data.response.error.message or "no message"}). " +
        "Make sure you filled the form correctly. " +
        "Please contact support if the error will not go away."
  )
])
