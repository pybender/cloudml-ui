'use strict'

### Tests specific Controllers ###

angular.module('app.testresults.controllers', ['app.config', ])

.controller('TestDialogController', [
  '$scope'
  'dialog'
  '$location'
  'TestResult'

($scope, dialog, $location, Test) ->

  $scope.parameters = {} # parameters to send via API
  $scope.model = dialog.model
  $scope.model.$load(show: 'import_params').then (->
    $scope.params = $scope.model.import_params
  ), ((opts) ->
    $scope.setError(opts, 'loading model import parameters')
  )

  $scope.close = ->
    dialog.close()

  $scope.start = () ->
    data = {}
    for key of $scope.parameters
      data[key] = $scope.parameters[key]

    $scope.test = new Test({model_id: $scope.model._id})
    $scope.test.$run(data).then (->
      $location.path $scope.test.objectUrl()
      dialog.close()
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

($scope, $routeParams, Test, $location) ->
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

  DEFAULT_ACTION = 'test:details'
  $scope.action = ($routeParams.action or DEFAULT_ACTION).split ':'
  $scope.$watch 'action', (action) ->
    actionString = action.join(':')
    $location.search(
      if actionString == DEFAULT_ACTION then ""
      else "action=#{actionString}")

    switch action[0]
      when "curves" then $scope.goMetrics()
      when "matrix" then $scope.go 'status,metrics.confusion_matrix'
      else $scope.go 'name,status,classes_set,created_on,accuracy,
parameters,error,examples_count'

  $scope.go = (fields, callback) ->
    $scope.test.$load(
      show: fields
      ).then (->
        if callback?
          callback()
      ), ((opts)->
        $scope.setError(opts, 'loading test')
      )

  $scope.goMetrics = (fields, callback) ->
    $scope.go('status,metrics.roc_curve,
metrics.precision_recall_curve,metrics.roc_auc',
    () =>
      $scope.rocCurve = {'ROC curve': $scope.test.metrics.roc_curve}
      pr = $scope.test.metrics.precision_recall_curve
      $scope.prCurve = {'Precision-Recall curve': [pr[1], pr[0]]}
    )
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
