'use strict'

### Tests examples specific Controllers ###

angular.module('app.datas.controllers', ['app.config', ])

.controller('TestExamplesCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Data'
  'Model'
  'TestResult'

($scope, $routeParams, $location, Data, Model, Test) ->
  $scope.filter_opts = $location.search() # Used in ObjectListCtrl.
  $scope.simple_filters = {} # Filters by label and pred_label
  $scope.data_filters = [] # Filters by data_input.* fields
  for key, val of $scope.filter_opts
    if key != 'label' && key != 'pred_label'
      item = {name: key, value: val}
      $scope.data_filters.push(item)
    else
      $scope.simple_filters[key] = val

  $scope.init = (test) ->
    $scope.test = test
    Data.$loadFieldList(test.model_id, test._id).then ((opts) ->
      $scope.fields = opts.fields
    ), ((opts) ->
      $scope.setError(opts, 'loading data field list')
    )

    $scope.model = new Model({_id: $scope.test.model_id})
    $scope.model.$load(show: 'name,labels').then (->
      $scope.labels = $scope.model.labels
    ), ((opts) ->
      $scope.setError(opts, 'loading model')
    )

  $scope.loadDatas = () ->
    (opts) ->
      filter_opts = opts.filter_opts
      delete opts.filter_opts
      show = 'id,name,label,pred_label,title, probs'
      opts = _.extend({show: show}, opts, filter_opts)
      Data.$loadAll($scope.test.model_id, $scope.test._id,opts)

  $scope.addFilter = () ->
    $scope.data_filters.push({name: '', value: ''})

  $scope.filter = () ->
    data_filters = {}
    search_params = {}
    for item in $scope.data_filters
      if item.name
        data_filters[item.name] = item.value
    $scope.filter_opts = _.extend($scope.simple_filters, data_filters)
    $location.search($scope.filter_opts)

  $scope.filter()
])

.controller('GroupedExamplesCtrl', [
  '$scope'
  '$routeParams'
  'Data'
  'TestResult'

($scope, $routeParams, Data, Test) ->
  $scope.form = {'field': "", 'count': 2 }
  $scope.test = new Test({
    model_id: $routeParams.model_id,
    _id: $routeParams.test_id
  })
  $scope.test.$load(
      show: 'name'
  )
  Data.$loadFieldList($routeParams.model_id,
                      $routeParams.test_id).then ((opts) ->
      $scope.fields = opts.fields
    ), ((opts) ->
      $scope.setError(opts, 'loading data field list')
    )

  $scope.update = () ->
    Data.$loadAllGroupped($routeParams.model_id, $routeParams.test_id, {
      field: 'data_input.' + $scope.form.field,
      count: $scope.form.count
    }).then ((opts) ->
      $scope.field_name = opts.field_name
      $scope.mavp = opts.mavp
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading test examples')
    )
])

.controller('ExampleDetailsCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'Data'

($scope, $http, $routeParams, settings, Data) ->
  if not $scope.data
    $scope.data = new Data({
      model_id: $routeParams.model_id,
      test_id: $routeParams.test_id,
      _id: $routeParams.id
    })

  $scope.data.$load(
    show: "id,weighted_data_input,target_variable,pred_label,label,prob"
  ).then (->
    ), ((opts)->
      $scope.setError(opts, 'loading test example')
    )
])