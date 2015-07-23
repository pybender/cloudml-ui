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
  $scope.filter_opts = $location.search() or {} # Used in ObjectListCtrl.
  $scope.simple_filters = {} # Filters by label and pred_label
  $scope.data_filters = {} # Filters by data_input.* fields
  $scope.loading_state = false
  $scope.sort_by = $scope.filter_opts['sort_by'] or ''
  $scope.asc_order = $scope.filter_opts['order'] != 'desc'
  $scope.keysf = Object.keys

  $scope.init = (test, extra_params={'action': 'examples:list'}) ->
    $scope.extra_params = extra_params
    $scope.test = test
    $scope.loading_state = true

    Data.$loadFieldList($scope.test.model_id,
      $scope.test.id)
    .then (opts) ->
      $scope.fields = opts.fields
      for key, val of $scope.filter_opts
        key_name = key.replace("data_input->>", "")
        if key_name in $scope.fields
          $scope.data_filters[key] = val
        else if key == 'label' || key == 'pred_label'
          $scope.simple_filters[key] = val
      $scope.filter()
      $scope.loading_state = false
    , (opts) ->
      $scope.setError(opts, 'loading data field list')
      $scope.loading_state = false

    $scope.model = new Model({id: $scope.test.model_id})
    $scope.model.$load(show: 'name,labels').then (->
      $scope.labels = $scope.model.labels
    ), ((opts) ->
      $scope.setError(opts, 'loading model')
    )

  $scope.loadDatas = () ->
    (opts) ->
      filter_opts = opts.filter_opts
      delete opts.filter_opts
      show = 'id,name,label,pred_label,title,prob,example_id'
      opts = _.extend({show: show}, opts, filter_opts)
      $scope.loading_state = true
      opts.sort_by = $scope.sort_by
      opts.order = if $scope.asc_order then 'asc' else 'desc'
      Data.$loadAll($scope.test.model_id, $scope.test.id, opts)
      .then (resp) ->
        $scope.loading_state = false
        return resp
      , ->
        $scope.loading_state = false

  $scope.sort = (sort_by) ->
    if $scope.sort_by == sort_by
      # Only change ordering
      $scope.asc_order = !$scope.asc_order
    else
      # Change sort by field
      $scope.asc_order = true
      $scope.sort_by = sort_by
    $location.search($scope.getParamsDict())
    # TODO: nader20140916, what is this? @
    @load()

  $scope.addFilter = () ->
    $scope.data_filters.push({name: '', value: ''})

  $scope.appendDataFieldFilter = (key, value) ->
    $scope.data_filters[key] = value
    $scope.filter()
    $scope.dataField = null
    $scope.dataValue = null

  $scope.removeDataFieldFilter = (key) ->
    delete $scope.data_filters[key]
    $scope.filter()

  $scope.removeSimpleFieldFilter = (key) ->
    delete $scope.simple_filters[key]
    $scope.filter()

  $scope.filter = () ->
    opts = {}
    $scope.filter_opts = _.extend(opts, $scope.extra_params, $scope.simple_filters,
        $scope.data_filters)
    delete opts['action']
    $scope.filter_opts = opts
    $location.search($scope.getParamsDict())

  $scope.details = (example) ->
    $location.url(example.objectUrl()).search($scope.getParamsDict())

  $scope.getParamsDict = () ->
    sort_opts = {
      sort_by: $scope.sort_by
      order: if $scope.asc_order then 'asc' else 'desc'
    }
    res = _.extend(sort_opts, $scope.filter_opts)
    delete res['action']
    return res

  $scope.getExampleUrl = (example) ->
    example.objectUrl() + '?' + $.param($scope.getParamsDict())
])

.controller('GroupedExamplesCtrl', [
  '$scope'
  '$routeParams'
  'Data'
  'TestResult'

($scope, $routeParams, Data, Test) ->
  $scope.form = {'field': "", 'count': 2 }
  $scope.loading_state = true
  $scope.test = new Test({
    model_id: $routeParams.model_id,
    id: $routeParams.test_id
  })
  $scope.test.$load(
      show: 'name,examples_fields'
  ).then ((opts) ->
      $scope.loading_state = false
  ), ((opts) ->
      $scope.setError(opts, 'loading test details')
      $scope.loading_state = true
  )

  $scope.update = () ->
    if not $scope.form.field
      $scope.setError({}, 'Please, select a field')
      return
    $scope.loading_state = true
    Data.$loadAllGroupped($routeParams.model_id, $routeParams.test_id, {
      field: $scope.form.field,
      count: $scope.form.count})
    .then ((opts) ->
      $scope.field_name = opts.field_name
      $scope.mavp = opts.mavp
      $scope.objects = opts.objects
      $scope.loading_state = false
    ), ((opts) ->
      $scope.setError(opts, 'loading test examples')
      $scope.loading_state = false
    )
])

.controller('ExampleDetailsCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Data'

($scope, $routeParams, $location, TestExample) ->
  if not $scope.data
    $scope.data = new TestExample({
      model_id: $routeParams.model_id,
      test_id: $routeParams.test_id,
      id: $routeParams.id
    })

  # used for getting next/prev example ids
  $scope.filter_opts = $location.search()
  $scope.loaded = false

  $scope.goSection = () ->
    if $scope.loaded
      return

    loadParams = _.extend(
      {show: ['test_name','weighted_data_input','model', 'pred_label',
              'label','prob', 'created_on', 'test_result', 'next', 'previous',
              'parameters_weights', 'data_input'].join(',')}, $scope.filter_opts)
    $scope.data.$load loadParams
    .then ->
      $scope.loaded = true
    , (opts)->
      $scope.loaded = false
      $scope.setError(opts, 'loading test example')

  $scope.initSections($scope.goSection)

  $scope.next = ->
    $scope.redir({
      next: true
    })

  $scope.previous = ->
    $scope.redir({
      next: false
    })

  $scope.back = ->
    url = $scope.data.listUrl()
    $location.url(url)\
      .search(_.extend({action: 'examples:list'}, $scope.filter_opts))

  $scope.redir = (opts) ->
    if opts.next
      example_id = $scope.data.next
    else
      example_id = $scope.data.previous

    if !example_id?
      throw new Error('ERR: Prev or Next should be disabled!')

    example = new TestExample({
      model_id: $routeParams.model_id,
      test_id: $routeParams.test_id,
      id: example_id
    })
    $location.url(example.objectUrl()).search($scope.filter_opts)
])

# TODO: rename because it used for export to DB elso
# Choose fields to download classification results in CSV dialog controller
.controller('CsvDownloadCtrl', [
  '$scope'
  'openOptions'
  'Data'
  '$location'
  '$rootScope'

  ($scope, openOptions, Data, $location, $rootScope) ->
    # Field list to be displayed in choose field select
    $scope.selectFields = []
    $scope.extraData = {}

    $scope.csvField = ''
    $scope.stdFields = ['label', 'pred_label', 'prob']
    $scope.extraFields = []

    $scope.loading_state = true

    $scope.test = openOptions.model
    Data.$loadFieldList($scope.test.model_id,
      $scope.test.id)
    .then (opts) ->
      $scope.extraFields = opts.fields
      $scope.selectFields = []
      $scope.loading_state = false
    , (opts) ->
      $scope.setError(opts, 'loading data field list')
      $scope.loading_state = false

    $scope.appendField = (csvField) ->
      # TODO: Why do we not see csvField from scope in the controller?
      $scope.csvField = csvField
      if !!$scope.csvField and $scope.csvField not in $scope.extraFields and
          $scope.csvField in $scope.selectFields
        $scope.extraFields.push $scope.csvField
        $scope.selectFields = $scope.selectFields.filter (f) ->
            f isnt $scope.csvField
        $scope.selectFields = _.sortBy $scope.selectFields, (f)-> f
        $scope.csvField = ''

    $scope.addAll = ()->
      for field in $scope.selectFields
        if field not in $scope.extraFields
          $scope.extraFields.push field
      $scope.selectFields = []

    $scope.removeField = (fieldname) ->
      $scope.extraFields = $scope.extraFields.filter (f) ->
        f isnt fieldname
      if fieldname not in  $scope.selectFields
        $scope.selectFields.push fieldname
        $scope.selectFields = _.sortBy $scope.selectFields, (f)-> f

    $scope.removeAll = ()->
      for field in $scope.extraFields
        if field not in  $scope.selectFields
          $scope.selectFields.push field
      $scope.extraFields = []
      $scope.selectFields = _.sortBy $scope.selectFields, (f)-> f

    $scope.getExamplesCsv = () ->
      $scope.loading_state = true
      fields = $scope.stdFields.concat $scope.extraFields
      $scope.test.$get_examples_csv(fields)
      .then () ->
        $scope.loading_state = false
        $location.search('action=about:details')
        $scope.close()
        $rootScope.$broadcast 'exportsChanged'
      , (opts) ->
        $scope.setError(opts, 'failed submitting csv generation request')
        $scope.loading_state = false

    $scope.exportExamplesToDb = () ->
      $scope.loading_state = true
      fields = $scope.stdFields.concat $scope.extraFields
      $scope.test.$get_examples_db(
        _.extend {'fields': fields}, $scope.extraData)
      .then () ->
        $scope.loading_state = false
        $location.search('action=about:details')
        $scope.close()
        $rootScope.$broadcast 'exportsChanged'
      , (opts) ->
        $scope.setError(opts, 'failed submitting export to db request')
        $scope.loading_state = false

    $scope.close = () ->
      $scope.$close(true)
  ])
