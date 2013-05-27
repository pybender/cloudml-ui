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
  if not ($routeParams.model_id  and $routeParams.test_id)
      throw new Error "Can't initialize examples list controller
without test id and model id"
  $scope.filter_opts = $location.search()
  $scope.new_filters = {}
  $scope.data_filters = []
  for key, val of $scope.filter_opts
    if key != 'label' && key != 'pred_label'
      $scope.data_filters.push({name: key, value: val})
    else
      $scope.new_filters[key] = val
  
  Data.$loadFieldList($routeParams.model_id,
                      $routeParams.test_id).then ((opts) ->
    $scope.fields = opts.fields
  ), ((opts) ->
    $scope.setError(opts, 'loading data field list')
  )

  $scope.test = new Test({
    model_id: $routeParams.model_id,
    _id: $routeParams.test_id
  })
  $scope.test.$load(
      show: 'name'
  )

  $scope.model = new Model({_id: $routeParams.model_id})
  $scope.model.$load(
      show: 'name,labels'
  ).then (->
    $scope.labels = $scope.model.labels
  ), ((opts) ->
    $scope.setError(opts, 'loading model')
  )

  $scope.$watch('data_filters', (data_filters, oldVal, scope) ->
    for item in data_filters
      if item.name
        $scope.new_filters[item.name] = item.value
  , true)

  $scope.$watch('new_filters', (new_filters, oldVal, scope) ->
      $location.search(new_filters)
    , true)

  $scope.loadDatas = () ->
    (opts) ->
      filter_opts = opts.filter_opts
      delete opts.filter_opts
      show = 'id,name,label,pred_label,title, probs'
      opts = _.extend({show: show}, opts, filter_opts)
      Data.$loadAll($routeParams.model_id, $routeParams.test_id,
                    opts)

  $scope.addFilter = () ->
    $scope.data_filters.push({name: '', value: ''})

  $scope.filter = () ->
    $scope.filter_opts = $scope.new_filters

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