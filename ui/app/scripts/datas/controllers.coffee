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

  $scope.model = new Model({_id: $routeParams.model_id})
  $scope.test = new Test({
    model_id: $routeParams.model_id,
    _id: $routeParams.test_id
  })
  $scope.test.$load(
      show: 'name'
  )

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
    (opts) ->
      filter_opts = opts.filter_opts
      delete opts.filter_opts
      show = 'id,name,label,pred_label,title, probs'
      opts = _.extend({show: show}, opts, filter_opts)
      Data.$loadAll($routeParams.model_id, $routeParams.test_id,
                    opts)
])

.controller('GroupedExamplesCtrl', [
  '$scope'
  '$routeParams'
  'Data'
  'TestResult'

($scope, $routeParams, Data, Test) ->
  $scope.form = {'field': "data_input.hire_outcome", 'count': 2 }
  $scope.test = new Test({
    model_id: $routeParams.model_id,
    _id: $routeParams.test_id
  })
  $scope.test.$load(
      show: 'name'
  )
  $scope.update = () ->
    Data.$loadAllGroupped($routeParams.model_id, $routeParams.test_id, {
      field: $scope.form.field,
      count: $scope.form.count
    }).then ((opts) ->
      $scope.field_name = opts.field_name
      $scope.mavp = opts.mavp
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading test examples')
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