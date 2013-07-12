'use strict'

### Tests examples specific Controllers ###

angular.module('app.datas.controllers', ['app.config', ])

.controller('TestExamplesCtrl', [
  '$scope'
  '$rootScope'
  '$location'
  'Data'
  'Model'

($scope, $rootScope, $location, Data, Model) ->
  $scope.filter_opts = $location.search() # Used in ObjectListCtrl.
  $scope.simple_filters = {} # Filters by label and pred_label
  $scope.data_filters = [] # Filters by data_input.* fields

  $scope.init = (test, extra_params={'action': 'examples:list'}) ->
    $scope.extra_params = extra_params
    $scope.test = test
    Data.$loadFieldList(test.model_id, test._id).then ((opts) ->
      $scope.fields = opts.fields
      # Init search form
      for key, val of $scope.filter_opts
        key_name = key.replace("data_input.", "")
        if key_name in $scope.fields
          $scope.data_filters.push({name: key, value: val})
        else if key == 'label' || key == 'pred_label'
          $scope.simple_filters[key] = val
      $scope.filter()
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
      Data.$loadAll($scope.test.model_id, $scope.test._id, opts)

  $scope.addFilter = () ->
    $scope.data_filters.push({name: '', value: ''})

  $scope.filter = () ->
    data_filters = {}
    search_params = {}
    for item in $scope.data_filters
      if item.name
        data_filters[item.name] = item.value
    $scope.filter_opts = _.extend($scope.simple_filters, data_filters,
                                  $scope.extra_params)
    $location.search($scope.filter_opts)
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
    show: "id,test_name,weighted_data_input,target_variable,
pred_label,label,prob"
  ).then (->
    ), ((opts)->
      $scope.setError(opts, 'loading test example')
    )
])

# Choose fields to download classification results in CSV dialog controller
.controller('CsvDownloadCtrl', [
  '$scope'
  'dialog'
  'Data'

  ($scope, dialog, Data) ->
    # Field list to be displayed in choose field select
    $scope.selectFields = []

    $scope.csvField = ''
    $scope.csvFields = ['name', 'id', 'label', 'pred_label', 'prob']
    $scope.show = 'name,id,label,pred_label,prob'

    $scope.test = dialog.model
    Data.$loadFieldList($scope.test.model_id,
      $scope.test._id).then ((opts) ->
      $scope.selectFields = ("data_input." + x for x in opts.fields)
    ), ((opts) ->
      $scope.setError(opts, 'loading data field list')
    )

    $scope.appendField = () ->
      if !!$scope.csvField
        $scope.csvFields.push $scope.csvField
        $scope.show = $scope.csvFields.join(',')
        $scope.selectFields = $scope.selectFields.filter (f) ->
            f isnt $scope.csvField
        $scope.csvField = ''

    $scope.removeField = (fieldname) ->
      $scope.csvFields = $scope.csvFields.filter (f) ->
        f isnt fieldname
      $scope.show = $scope.csvFields.join(',')
      $scope.selectFields.push fieldname

    $scope.close = () ->
      dialog.close()
  ])
