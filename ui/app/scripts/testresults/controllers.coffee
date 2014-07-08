'use strict'

### Tests specific Controllers ###
angular.module('app.testresults.controllers', ['app.config', ])

.controller('TestListCtrl', [
  '$scope'
  '$dialog'
  '$rootScope'
  'TestResult'

  ($scope, $dialog, $rootScope, TestResult) ->
    $scope.MODEL = TestResult
    $scope.FIELDS = 'name,created_on,status,parameters,accuracy,examples_count,
created_by'
    $scope.ACTION = 'loading tests'

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
  'dialog'
  '$location'
  'TestResult'

  ($scope, dialog, $location, Test) ->
    $scope.dialog = dialog
    $scope.resetError()
    $scope.model = dialog.model
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
        dialog.close()
        $location.path $scope.test.objectUrl()
      ), ((opts) ->
        $scope.setError(opts, 'running test')
      )
])

.controller('DeleteTestCtrl', [
  '$scope'
  'dialog'
  '$location'

  ($scope, dialog, location) ->
    $scope.test = dialog.test
    $scope.model = dialog.test.model
    $scope.resetError()

    $scope.close = ->
      dialog.close()

    $scope.delete = (result) ->
      $scope.test.$delete().then (() ->
        $scope.close()
#        location.search('action=test:list&any=' + Math.random())
        $scope.$emit('modelDeleted', [$scope.model])
        $scope.$broadcast('modelDeleted', [$scope.model])
      ), ((opts) ->
        $scope.setError(opts, 'deleting test')
      )
])

.controller('TestDetailsCtrl', [
  '$scope'
  '$routeParams'
  'TestResult'
  '$location'
  '$rootScope'
  '$dialog'

($scope, $routeParams, Test, $location, $rootScope, $dialog) ->
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
          extra_fields = 'accuracy,metrics'
          cb = () ->
            $scope.rocCurve = {'ROC curve': $scope.test.metrics.roc_curve}
            pr = $scope.test.metrics.precision_recall_curve
            $scope.prCurve = {'Precision-Recall curve': [pr[1], pr[0]]}
               
        when 'matrix' then extra_fields = Test.MATRIX_FIELDS

      if 'main' in $scope.LOADED_SECTIONS
        # Do not need load main fields -> only extra
        if extra_fields != ''
          $scope.load(extra_fields, name, cb)
      else
        show = extra_fields + ',examples_placement,' + Test.MAIN_FIELDS
        $scope.load(show, name, cb)
        $scope.LOADED_SECTIONS.push 'main'

  $scope.downloadCsvResults = () ->
    $scope.openDialog({
        $dialog: $dialog
        model: $scope.test
        template: 'partials/datasets/csv_list_popup.html'
        ctrlName: 'CsvDownloadCtrl'
    })

  $scope.initSections($scope.goSection, 'metrics:accuracy')
])

.controller('TestActionsCtrl', [
  '$scope'
  '$dialog'

  ($scope, $dialog) ->
    $scope.init = (opts) ->
      test = opts.test
      model = opts.model
      if not test || not model
        throw new Error "Please specify test and model"

      opts.test.model = model
      $scope.test = test

    $scope.delete_test = (model) ->
      d = $dialog.dialog(
        modalFade: false
      )
      d.test = $scope.test
      d.open('partials/testresults/delete_popup.html', 'DeleteTestCtrl')
  
])

.controller('TestExportsCtrl', [
  '$scope'

  ($scope) ->
    $scope.exports = []

    $scope.init = (test) ->
      $scope.test = test
      $scope.reload()

    $scope.reload = () ->
      $scope.test.$get_exports().then((resp) ->
        $scope.exports = resp.data.exports
        statuses = []
        statuses.push e.status for e in $scope.exports
        if 'In Progress' in statuses
          window.setTimeout(
            () ->$scope.reload()
            1000)
      )

    $scope.$on('exportsChanged', () ->
      window.setTimeout(
        () -> $scope.reload()
        1000)
    )
])

.controller('TestConfusionMatrixCtrl', [
  '$scope'

  ($scope) ->
    $scope.open_calc_id = null
    $scope.confusion_matrix_weights = {w0: 1, w1: 1, error: undefined}

    $scope.init = (test) ->
      $scope.test = test

    $scope.recalculate = (weight0, weight1) ->
      $scope.test.$get_confusion_matrix(weight0, weight1).then((resp) ->
        $scope.confusion_matrix_weights.error = resp.data.error
        window.setTimeout(
          () -> $scope.reload()
          100)
      )

    $scope.showResult = (id) ->
      if $scope.open_calc_id == id
        $scope.open_calc_id = null
      else
        $scope.open_calc_id = id

    $scope.reload = () ->
      $scope.test.$load({show: 'confusion_matrix_calculations'}).then((resp) ->
        statuses = []
        statuses.push c.status for c in ($scope.test
        .confusion_matrix_calculations)
        if 'In Progress' in statuses
          window.setTimeout(
            () -> $scope.reload()
            1000)
      )
])
