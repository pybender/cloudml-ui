'use strict'

### Tests specific Controllers ###

angular.module('app.testresults.controllers', ['app.config', ])

.controller('TestDialogController', [
  '$scope'
  '$http'
  'dialog'
  'settings'
  '$location'
  'TestResult'

($scope, $http, dialog, settings, $location, Test) ->

  $scope.model = dialog.model
  $scope.model.$load(
    show: 'import_params'
    ).then (->
      $scope.params = $scope.model.import_params
    ), (->
      $scope.err = data
    )
  $scope.parameters = {} # parameters to send via API

  $scope.close = ->
    dialog.close()

  $scope.start = (result) ->
    form_data = new FormData()
    model = $scope.model
    for key of $scope.parameters
      form_data.append(key, $scope.parameters[key])

    $http(
      method: "POST"
      url: settings.apiUrl + "model/#{model.name}/test/test"
      data: form_data
      headers: {'Content-Type':undefined, 'X-Requested-With': null}
      transformRequest: angular.identity
    ).success((data, status, headers, config) ->
      $scope.success = true
      data['test']['model_name'] = model.name
      test = new Test(data['test'])
      $location.path test.objectUrl()
      dialog.close(result)
    ).error((data, status, headers, config) ->
      $scope.httpError = true
    )
])

.controller('DeleteTestCtrl', [
  '$scope'
  '$http'
  'dialog'
  'settings'
  '$location'

  ($scope, $http, dialog, settings, location) ->
    $scope.test = dialog.test
    $scope.model = dialog.test.model

    $scope.close = ->
      dialog.close()

    $scope.delete = (result) ->
      $scope.test.$delete().then (() ->
        $scope.close()
        location.search('action=test:list&any=' + Math.random())
      ), ((opts) ->
        if opts.data
          $scope.err = "Error while deleting test:" +
            "server responded with " + "#{opts.status} " +
            "(#{opts.data.response.error.message or "no message"}). "
        else
          $scope.err = "Error while deleting test"
      )
])

.controller('TestDetailsCtrl', [
  '$scope'
  '$http'
  '$routeParams'
  'settings'
  'TestResult'
  '$location'

($scope, $http, $routeParams, settings, Test, $location) ->
  if not $scope.test
    if not $routeParams.name
      throw new Error "Can't initialize test detail controller
      without test name"

    $scope.test = new Test({model_name: $routeParams.name,
    name: $routeParams.test_name})
    $scope.test_num = $routeParams.test_name

  $scope.log_messages = []
  log_sse = new EventSource("#{settings.apiUrl}log/")
  handleCallback = (msg) ->
    $scope.$apply(() ->
      if msg?
        data = JSON.parse(msg.data)
        action = data['k']
        id = data['data']['test']
        if action == 'runtest_log' and id == $scope.test._id
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
        loaded_var = true
        if callback?
          callback()
      ), (->
        $scope.err = 'Error'
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
