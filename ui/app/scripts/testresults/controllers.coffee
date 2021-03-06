'use strict'

### Tests specific Controllers ###
angular.module('app.testresults.controllers', ['app.config', ])

.controller('TestListCtrl', [
  '$scope'
  '$rootScope'
  'TestResult'

  ($scope, $rootScope, TestResult) ->
    $scope.MODEL = TestResult
    $scope.keysf = Object.keys
    $scope.FIELDS = 'name,created_on,status,parameters,accuracy,examples_count,\
created_by,roc_auc'
    $scope.ACTION = 'loading tests'
    $scope.filter_opts = {'sort_by': 'id', 'order': 'desc'}

    $scope.$on('loadTest', (event, opts) ->
      setTimeout(() ->
        $scope.$emit('BaseListCtrl:start:load', 'testresult')
      , 100)
    )

    $scope.init = (model) ->
      $scope.model = model
      $scope.kwargs = {'model_id': model.id}
])

.controller('TestDialogController', [
  '$scope'
  '$location'
  'TestResult'
  'openOptions'

  ($scope, $location, Test, openOptions) ->
    $scope.resetError()
    $scope.model = openOptions.model
    $scope.handler = $scope.model.test_import_handler_obj

    $scope.data = {}

    # Choose examples fields select options
    $scope.test_handler_fields = []
    angular.forEach($scope.model.test_handler_fields, (item, key) ->
      $scope.test_handler_fields.push({text: item, id: item})
    )
    $scope.select2params = {
      multiple: true,
      simple_tags: true,
      tags: $scope.model.test_handler_fields
    }

    $scope.start = (result) ->
      $scope.test = new Test({model_id: $scope.model.id})
      $scope.test.$run($scope.data).then (->
        $scope.$close(true)
        $location.path $scope.test.objectUrl()
      ), ((opts) ->
        $scope.setError(opts, 'running test')
      )
])

# TODO: nader20140901 - should be removed along with partials/testresults/delete_popup.html
# we are now using DialogCtrl (see TestActionsCtrl)
#.controller('DeleteTestCtrl', [
#  '$scope'
#  '$location'
#  'openOptions'
#
#  ($scope, location, openOptions) ->
#    $scope.test = openOptions.test
#    $scope.model = openOptions.test.model
#    $scope.resetError()
#
#    $scope.delete = (result) ->
#      $scope.test.$delete().then (() ->
#        $scope.$close(true)
##        location.search('action=test:list&any=' + Math.random())
#        $scope.$emit('modelDeleted', [$scope.model])
#        $scope.$broadcast('modelDeleted', [$scope.model])
#      ), ((opts) ->
#        $scope.setError(opts, 'deleting test')
#      )
#])

.controller('TestDetailsCtrl', [
  '$scope'
  '$routeParams'
  'TestResult'
  '$location'
  '$rootScope'
  '$timeout'

($scope, $routeParams, Test, $location, $rootScope, $timeout) ->
  $scope.LOADED_SECTIONS = []
  if not $scope.test
    if not ($routeParams.model_id and $routeParams.id)
      throw new Error "Can't initialize test details controller
without test id and model id"

    $scope.test = new Test({
      model_id: $routeParams.model_id,
      id: $routeParams.id
    })

  $scope.load = (fields, section, callback) ->
    $scope.test.$load(
      show: fields
      ).then (->
        $scope.LOADED_SECTIONS.push section
        $scope.showdetails = ($scope.test.status in ['Completed', 'Storing'])
        if $scope.test.status != 'Completed' && $scope.test.status != 'Storing'
          $scope.setSection(['about', 'details'])
          return

        if callback?
          callback()
      ), ((opts)->
        $scope.setError(opts, 'loading test')
      )

  $scope.goSection = (section) ->
    section_name = section[0]
    subsection_name = section[1]
    name = section_name + '-' + subsection_name
    cb = null
    if name not in $scope.LOADED_SECTIONS
      extra_fields = ''
      switch section_name
        when 'examples'
          extra_fields = 'classes_set'
        when 'about'
          extra_fields = Test.EXTRA_FIELDS
        when 'metrics'
          extra_fields = 'accuracy,metrics,roc_auc'
          cb = addMetricsToScope
        when 'matrix'
          extra_fields = Test.MATRIX_FIELDS
          cb = addConfusionMatrixWeightsToScope

      if 'main' in $scope.LOADED_SECTIONS
        # Do not need load main fields -> only extra
        if extra_fields isnt ''
          $scope.load(extra_fields, name, cb)
      else
        show = extra_fields + ',examples_placement,fill_weights,' + Test.MAIN_FIELDS
        $scope.load(show, name, cb)
        $scope.LOADED_SECTIONS.push 'main'

  $scope.downloadCsvResults = () ->
    $scope.openDialog($scope, {
        model: $scope.test
        template: 'partials/datasets/csv_list_popup.html'
        ctrlName: 'CsvDownloadCtrl'
    })

  $scope.exportResultsToDb = () ->
    $scope.openDialog($scope, {
        model: $scope.test
        template: 'partials/testresults/export_to_db_popup.html'
        ctrlName: 'CsvDownloadCtrl'
    })

  addMetricsToScope = ->
    metrics = $scope.test.metrics
    roc_auc = $scope.test.roc_auc or $scope.test.metrics.roc_auc
    $scope.rocCurves = {}
    if _.isObject(roc_auc)
      # new dict formate after 20140710
      classes = _.keys(metrics.roc_curve)
      for c in classes
        label =  if classes.length > 1 then 'ROC Curve For Class (' + c + ')'\
          else 'ROC Curve'
        curve = {}
        curve[label] = metrics.roc_curve[c]
        $scope.rocCurves[c] = {curve: curve, roc_auc: roc_auc[c]}
      if classes.length is 1 # only binary classifier publishes PR curve
        $scope.prCurves =
          # we are switching precision/recall positions. The dictionary
          # publishes them as [precision recall] while the chart has
          # precision @ y-axis and recall @ x-axis, and chart expects
          # [x-axis y-axis] soo we need the flip
          'Precision-Recall curve': [
            metrics.precision_recall_curve[1],
            metrics.precision_recall_curve[0]
          ]
    else
      # old list format
      $scope.rocCurves[1] =
        curve: {'ROC curve': $scope.test.metrics.roc_curve}
        roc_auc: roc_auc
      pr = $scope.test.metrics.precision_recall_curve
      $scope.prCurves = {'Precision-Recall curve': [pr[1], pr[0]]}

  addConfusionMatrixWeightsToScope = ->
    $scope.confusion_matrix_weights = []
    for label in $scope.test.model.labels
      $scope.confusion_matrix_weights.push({"label": label, "value": 1})

  $scope.test_timer = null
  $scope.monitorTesting = () ->
    $scope.test_timer = $timeout( ()->
        $scope.test.$load(
          show: 'status,test_in_progress,error'
        ).then (->
          if $scope.test.test_in_progress
            $scope.monitorTesting()
          else
            $scope.LOADED_SECTIONS = ['main']
            $scope.setSection($scope.action || ['metrics', 'accuracy'])
        )
      10000
    )

  $scope.$watch 'test.test_in_progress', (newVal, oldVal)->
    if newVal == true
      $scope.monitorTesting()

  $scope.$on '$destroy', (event) ->
    $timeout.cancel($scope.test_timer)

  $scope.initSections($scope.goSection, 'metrics:accuracy')
])

.controller('TestActionsCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (opts) ->
      test = opts.test
      model = opts.model
      if not test || not model
        throw new Error "Please specify test and model"

      opts.test.model = model
      $scope.test = test

    $scope.delete_test = (model) ->
      $scope.openDialog $scope,
        model: $scope.test
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete Test'
        path: $scope.test.model.objectUrl()
])

.controller('TestExportsCtrl', [
  '$scope'
  '$timeout'

  ($scope, $timeout) ->
    $scope.exports = []
    $scope.db_exports = []

    $scope.init = (test) ->
      $scope.test = test
      $scope.reload()

    $scope.reload = () ->
      $scope.test.$get_exports().then((resp) ->
        $scope.exports = resp.data.exports
        $scope.db_exports = resp.data.db_exports

        reloadInProgressTasks = (tasks) ->
          statuses = []
          statuses.push e.status for e in tasks
          if 'In Progress' in statuses
            $timeout ->
              $scope.reload()
            , 8000

        reloadInProgressTasks $scope.exports.concat($scope.db_exports)
      )

    $scope.$on('exportsChanged', () ->
      $timeout ->
        $scope.reload()
      , 5000
    )
])

.controller('TestConfusionMatrixCtrl', [
  '$scope'

  ($scope) ->
    $scope.open_calc_id = null
    $scope.open_logs_calc_id = null
    $scope.confusion_matrix_error = undefined
    $scope.in_progress_requests = false

    $scope.init = (test) ->
      $scope.test = test

    $scope.recalculate = () ->
      $scope.in_progress_requests = true
      $scope.test.$get_confusion_matrix(
                   $scope.confusion_matrix_weights).then((resp) ->
        $scope.confusion_matrix_error = resp.data.error
        window.setTimeout(
          () -> $scope.reload()
          100)
      )

    $scope.showResult = (id) ->
      if $scope.open_calc_id == id
        $scope.open_calc_id = null
      else
        $scope.open_calc_id = id

    $scope.showLogs = (id) ->
      if $scope.open_logs_calc_id == id
        $scope.open_logs_calc_id = null
      else
        $scope.open_logs_calc_id = id

    $scope.reload = () ->
      $scope.test.$load({show: 'confusion_matrix_calculations'}).then((resp) ->
        statuses = []
        statuses.push c.status for c in ($scope.test
        .confusion_matrix_calculations)
        if 'In Progress' in statuses
          $scope.in_progress_requests = true
          window.setTimeout(
            () -> $scope.reload()
            1000)
        else
          $scope.in_progress_requests = false
      )
])
