'use strict'

### Parameters weights specific Controllers ###

angular.module('app.weights.controllers', ['app.config', ])

.controller('WeightsCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  '$location'
  'Weight'
  'WeightsTree'

($scope, $http, $routeParams, $location, Weight, WeightsTree) ->
  if not $routeParams.id
    throw new Error "Can't initialize without model id"

  $scope.model_id = $routeParams.id

  # List search parameters and methods
  $scope.search_form = {'q': '', 'is_positive': 0}

  $scope.loadList = () ->
    Weight.$loadAll(
      $scope.model.id,
      show: 'name,value,css_class',
      q: $scope.search_form.q,
      is_positive: $scope.search_form.is_positive,
      page: $scope.search_form.page || 1
    ).then ((opts) ->
      $scope.weights = opts.objects
      $scope.total = opts.total
      $scope.search_form.page = opts.page || 1
      $scope.pages = opts.pages
      $scope.per_page = opts.per_page
    ), ((opts) ->
      $scope.err = "Error while loading parameters weights: " +
        "server responded with " + "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )

  $scope.$watch('search_form.page', (page, oldVal, scope) ->
        if (scope.action[0] == 'weights') and
            (scope.action[0] == 'list') and page
          $scope.loadList()
      , true)

  # Tree params & methods
  $scope.tree_dict = {'weights': {}, 'categories': {}}

  $scope.loadTreeNode = (parent, show) ->
    if not show
      return

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

  # Columns view parameters and methods
  $scope.ppage = 1
  $scope.npage = 1
  $scope.positive = []
  $scope.negative = []

  $scope.loadColumns = (morePositive, moreNegative) ->
    Weight.$loadBriefList(
      $scope.model_id,
      show: 'name,value,css_class'
      ppage: $scope.ppage
      npage: $scope.npage
      ).then ((opts) ->
        if morePositive
          $scope.positive.push.apply($scope.positive, opts.positive)
        if moreNegative
          $scope.negative.push.apply($scope.negative, opts.negative)
      ), ((opts)->
        $scope.err = opts
      )

  $scope.morePositiveWeights  = =>
    $scope.ppage += 1
    $scope.loadColumns(true, false)

  $scope.moreNegativeWeights  = =>
    $scope.npage += 1
    $scope.loadColumns(false, true)

  # Switching modes methods
  $scope.$watch 'action', (action) ->
    if action[0] == 'weights'
      actionString = action.join(':')
      $location.search("action=#{actionString}")
      view = action[1]
      switch view
        when "columns" then $scope.loadColumns(true, true)
        when "list" then  $scope.loadList('', 1)
        when "tree" then $scope.loadTreeNode('', true)
])