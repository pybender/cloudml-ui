'use strict'

### Trained Model specific Controllers ###

angular.module('app.reports.controllers', ['app.config', ])


.controller('CompareModelsFormCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'Model'
  'TestResult'
  'Data'
  'CompareReport'

  ($scope, $http, $location, $routeParams, settings,
  Model, Test, Data, CompareReport) ->
    FORM_ACTION = 'form:'
    $scope.section = 'metrics'
    $scope.action = ($routeParams.action or FORM_ACTION).split ':'

    $scope.$watch 'action', (action) ->
      get_params = action[1].split ','
      if !$scope.report? && get_params.length != 0
        kwargs = {}
        for i in [0...get_params.length]
            param = get_params[i]
            num = Math.floor(i / 2 + 1)
            if i % 2 == 1
                kwargs['test_name' + num] = param
            else
                kwargs['model_name' + num] = param
        $scope.report = new CompareReport(kwargs)

      if action[0] == 'report'
        if !$scope.report.generated
            $scope.generate()
      else
        if action[0] == 'form'
          $scope.initForm()

      actionString = action.join(':')
      $location.search(
        if actionString == FORM_ACTION then ""
        else "action=#{actionString}")

    model_watcher = (model, oldVal, scope) ->
      if model?
        $scope.loadTestsList(model)

    $scope.$watch('model1', model_watcher, true)
    $scope.$watch('model2', model_watcher, true)

    $scope.is_form = ->
      $scope.action[0] == 'form'

    $scope.loadModelsList = =>
      Model.$loadAll({comparable: 1}
      ).then ((opts) ->
        $scope.models = opts.objects
        # TODO: Fix this
        if $scope.is_form()
          for m in $scope.models
            if m.name == $scope.report.model_name1
              $scope.model1 = m
            if m.name == $scope.report.model_name2
              $scope.model2 = m
      ), ((opts) ->
        err = opts.$error
      )

    $scope.loadTestsList = (model) =>
      Test.$loadTests(
        model.name, {status: "Completed"}
      ).then ((opts) ->
        model.tests = opts.objects
        # TODO: Fix this
        if $scope.is_form()
          for t in model.tests
            if (t.name == $scope.report.test_name1) &&
            (model.name == $scope.report.model_name1)
              $scope.test1 = t
            if (t.name == $scope.report.test_name2) &&
            (model.name == $scope.report.model_name2)
              $scope.test2 = t
      ), ((opts) ->
        err = opts.$error
      )

    $scope.backToForm = () =>
      $scope.toogleAction("form")

    $scope.generateReport = () =>
      # fill parameters from form
      kwargs = {test_name1: $scope.test1.name,
      model_name1: $scope.model1.name,
      test_name2: $scope.test2.name,
      model_name2: $scope.model2.name}
      $scope.report = new CompareReport(kwargs)
      $scope.toogleAction("report", "metrics")

    $scope.toogleAction = (action_name) =>
      report = $scope.report

      $scope.action = [action_name,
            "#{report.model_name1},#{report.test_name1}," +
            "#{report.model_name2},#{report.test_name2}"]

    $scope.toogleReportSection = (section) =>
      $scope.section = section

    $scope.initForm = () =>
      $scope.loadModelsList()

    $scope.generate = () =>
      $scope.generating = true
      $scope.generatingProgress = '0%'
      $scope.generatingError = null

      _.defer ->
        $scope.generatingProgress = '70%'
        $scope.$apply()

      $scope.report.$getReportData()
      .then (->
        $scope.generatingProgress = '100%'
        $scope.generating = false
        $scope.generated = true
      ), ((resp) ->
        $scope.generating = false
        $scope.err = "Error while generating compare report:" +
          "server responded with #{resp.status} " +
          "(#{resp.data.response.error.message or "no message"}). " +
          "Make sure you filled the form correctly. " +
          "Please contact support if the error will not go away."
      )

])
