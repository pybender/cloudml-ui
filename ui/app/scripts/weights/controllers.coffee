'use strict'

### Parameters weights specific Controllers ###

angular.module('app.weights.controllers', ['app.config', ])

.controller('WeightsListCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'Weight'
  '$location'

($scope, $http, $routeParams, settings, Weight, $location) ->
  if not $routeParams.name
    throw new Error "Can't initialize without model name"

  $scope.q = ''

  $scope.loadWeights = (search='', page=1) ->
    Weight.$loadAll(
      $routeParams.name,
      show: 'name,value,css_class',
      q: search,
      page: page,
      is_positive: $scope.is_positive
    ).then ((opts) ->
      $scope.weights = opts.objects
      $scope.total = opts.total
      $scope.page = opts.page || 1
      $scope.pages = opts.pages
      $scope.per_page = opts.per_page
    ), ((opts) ->
      $scope.err = "Error while loading parameters weights: " +
        "server responded with " + "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )

  $scope.loadWeights()

  $scope.$watch('page', (page, oldVal, scope) ->
        $scope.loadWeights($scope.q, page)
      , true)

  $scope.search = () ->
    $scope.loadWeights($scope.q)
])
