'use strict'

### Tests examples specific Controllers ###

angular.module('app.datas.controllers', ['app.config', ])

.controller('TestExamplesCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  '$location'
  'Data'
  'Model'
  'TestResult'

($scope, $http, $routeParams, settings, $location, Data, Model, Test) ->
  $scope.test_name = $routeParams.test_name
  $scope.filter_opts = $location.search()
  $scope.model = new Model({name: $routeParams.name})
  $scope.test = new Test({
    model_name: $routeParams.name, name: $routeParams.test_name})

  $scope.model.$load(
      show: 'name,labels'
  ).then (->
    $scope.labels = $scope.model.labels
    $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
      $location.search(filter_opts)
    , true)
  ), (->
    $scope.err = data
  )

  $scope.loadDatas = () ->
    # Used for ObjectListCtrl initialization
    (opts) ->
      filter_opts = opts.filter_opts
      delete opts.filter_opts
      Data.$loadAll(_.extend({model_name: $routeParams.name,
      test_name: $routeParams.test_name,
      show:'name,label,pred_label,title, probs'}, opts, filter_opts))
])

.controller('GroupedExamplesCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'Data'

($scope, $http, $routeParams, settings, Data) ->
  $scope.test_name = $routeParams.test_name
  $scope.model_name = $routeParams.name
  $scope.form = {'field': "data_input.hire_outcome", 'count': 2 }
  $scope.update = () ->
    Data.$loadAllGroupped(
      model_name: $routeParams.name
      test_name: $routeParams.test_name
      field: $scope.form.field,
      count: $scope.form.count
    ).then ((opts) ->
      $scope.field_name = opts.field_name
      $scope.mavp = opts.mavp
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.err = "Error while loading: server responded with " +
          "#{opts.status} " +
          "(#{opts.data.response.error.message or "no message"})."
    )
  $scope.update()
])

.controller('ExampleDetailsCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'Data'

($scope, $http, $routeParams, settings, Data) ->
  if not $scope.data
    $scope.data = new Data({model_name: $routeParams.name,
    test_name: $routeParams.test_name,
    id: $routeParams.data_id})

  $scope.data.$load(
    show: "id,weighted_data_input,target_variable,pred_label,label, probs"
  ).then (->
    ), (->
      $scope.error = data
      $scope.httpError = true
    )
])