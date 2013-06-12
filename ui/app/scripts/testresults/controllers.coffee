'use strict'

### Tests specific Controllers ###

angular.module('app.testresults.controllers', ['app.config', ])

.controller('TestDialogController', [
  '$scope'
  'dialog'
  '$location'
  'TestResult'

  ($scope, dialog, $location, Test) ->
    $scope.dialog = dialog
    $scope.parameters = {}
    $scope.model = dialog.model
    $scope.handler = $scope.model.test_import_handler_obj

    $scope.start = (result) ->
      data = {}
      for key of $scope.parameters
        data[key] = $scope.parameters[key]

      $scope.test = new Test({model_id: $scope.model._id})
      $scope.test.$run(data).then (->
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
        location.search('action=test:list&any=' + Math.random())
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

($scope, $routeParams, Test, $location, $rootScope) ->
  $scope.LOADED_SECTIONS = []
  if not $scope.test
    if not ($routeParams.model_id  and $routeParams.id)
      throw new Error "Can't initialize test details controller
without test id and model id"

    $scope.test = new Test({
      model_id: $routeParams.model_id,
      _id: $routeParams.id
    })

  $scope.$watch 'test.status', (status) ->
    if status in ['Queued', 'In Progress', 'Error']
      $scope.showLog = true
      $scope.log_messages = []
      params = "channel=runtest_log&test=" + $scope.test._id
      log_sse = $scope.getEventSourceTest(params=params)
      handleCallback = (msg) ->
        $scope.$apply(() ->
          if msg?
            data = JSON.parse(msg.data)
            $scope.log_messages.push(data['data']['msg']))
      log_sse.addEventListener('message', handleCallback)

  $scope.load = (fields, section, callback) ->
    $scope.test.$load(
      show: fields
      ).then (->
        $scope.LOADED_SECTIONS.push section
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
        when 'about'
          extra_fields = 'classes_set,created_on,parameters,error,
examples_count'
        when 'metrics'
          extra_fields = 'accuracy,metrics.precision_recall_curve,
metrics.roc_curve,metrics.roc_auc'
          cb = () =>
            $scope.rocCurve = {'ROC curve': $scope.test.metrics.roc_curve}
            pr = $scope.test.metrics.precision_recall_curve
            $scope.prCurve = {'Precision-Recall curve': [pr[1], pr[0]]}
               
        when 'matrix' then extra_fields = 'metrics.confusion_matrix'

      if 'main' in $scope.LOADED_SECTIONS
        # Do not need load main fields -> only extra
        if extra_fields != ''
          $scope.load(extra_fields, name, cb)
      else
        $scope.load(extra_fields + ',' + Test.MAIN_FIELDS, name, cb)
        $scope.LOADED_SECTIONS.push 'main'

  $scope.initSections($scope.goSection, defaultAction='metrics:accuracy')
])

.controller('TestActionsCtrl', [
  '$scope'
  '$dialog'

  ($scope, $dialog) ->
    $scope.init = (opts) =>
      test = opts.test
      model = opts.model
      if not test || not model
        throw new Error "Please specify test and model"

      opts.test.model = model
      $scope.test = test

    $scope.delete_test = (model)->
      d = $dialog.dialog(
        modalFade: false
      )
      d.test = $scope.test
      d.open('partials/testresults/delete_popup.html', 'DeleteTestCtrl')
  
])
