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
  $scope.is_positive = 0
  $scope.model_name = $routeParams.name

  $scope.loadWeights = (search='', page=1) ->
    Weight.$loadAll(
      $scope.model_name,
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
  'WeightsTree'

($scope, $http, $routeParams, settings, Weight, WeightsTree) ->
  if not $routeParams.name
    throw new Error "Can't initialize without model name"

  $scope.tree_dict = {'weights': {}, 'categories': {}}
  $scope.model_name = $routeParams.name

  $scope.loadNode = (parent='') ->
    if parent
        parent_list = parent.split('.')
        name = parent_list.shift()
        parent_node = $scope.tree_dict['categories'][name]
        for name in parent_list
          parent_node = parent_node['categories'][name]

        if parent_node['loaded']?
          return
      else
        parent_node = $scope.tree_dict

    WeightsTree.$loadNode(
      $routeParams.name,
      show: 'name,short_name,parent',
      parent: parent
    ).then ((opts) ->
      for details in opts.categories
        val = {'categories': {}, 'details': details, 'weights': {}}
        parent_node['categories'][details.short_name] = val

      for details in opts.weights
        parent_node['weights'][details.name] = details

      parent_node['loaded'] = true
    ), ((opts) ->
      $scope.err = "Error while loading parameters weights: " +
        "server responded with " + "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )

  $scope.load = (parentCategory, show) ->
    if show
      $scope.loadNode(parentCategory.name)

  $scope.loadNode()
])
