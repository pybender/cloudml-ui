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



.controller('WeightsTreeCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'Weight'
  'WeightsCategory'

($scope, $http, $routeParams, settings, Weight, WeightsCategory) ->
  if not $routeParams.name
    throw new Error "Can't initialize without model name"

  $scope.tree_dict = {}

  $scope.loadWeightsCategories = (parent='', load_weights='False') ->
    WeightsCategory.$loadAll(
      $routeParams.name,
      show: 'name,short_name,parent,has_weights',
      parent: parent
    ).then ((opts) ->
      $scope.categories = opts.objects
      for cat in $scope.categories
        val = {'subcategories': {}, 'details': cat}
        if !parent
          $scope.tree_dict[cat.name] = val
        else
          $scope.tree_dict[parent]['subcategories'][cat.name] = val
      if load_weights == 'True'
        alert('load' + load_weights)
    ), ((opts) ->
      $scope.err = "Error while loading parameters weights: " +
        "server responded with " + "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )

  $scope.load = (parentCategory) ->
    alert(parentCategory.name)
    $scope.loadWeightsCategories(parentCategory.name,
      parentCategory.has_weights)

  $scope.loadWeightsCategories()
])
