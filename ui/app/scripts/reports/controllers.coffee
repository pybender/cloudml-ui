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
    FORM_ACTION = 'form'
    $scope.action = ($routeParams.action or FORM_ACTION).split ':'
    $scope.section = 'metrics' # section of report view

    $scope.form_data = [{'model': null, 'test': null},
                        {'model': null, 'test': null}]

    $scope.$watch 'action', (action, oldAction) ->
      # to avoid the initialization call as per docs
      if action is oldAction
        return

      # Parsing get parameters:
      #   model_id1,test_id1...model_idN,test_idN
      get_params = []
      if action[1]
        get_params = action[1].split ','
      if !$scope.report? && get_params.length != 0
        data = []
        for i in [0...get_params.length]
            param = get_params[i]
            num = Math.floor(i / 2 + 1)
            if i % 2 == 1
                val['test'] = {'id': param}
                data.push(val)
            else
                val = {'model': {'id': param}}
        $scope.form_data = data
        $scope.report = new CompareReport(data)

      if action[0] == 'report'
        if !$scope.report.generated
            $scope.generate()
      else
        $scope.initForm()

      actionString = action.join(':')
      $location.search(
        if actionString == FORM_ACTION then ""
        else "action=#{actionString}")

    $scope.initForm = () ->
      Model.$loadAll({comparable: 1, show: "name"}
      ).then ((opts) ->
        $scope.comparable_models = []
        for model in opts.objects
          $scope.comparable_models.push({'id': model.id, 'name': model.name})
      ), ((opts) ->
        $scope.setError(opts, 'loading models')
      )

    $scope.changeModel = (item) ->
      item.avaiable_tests = []
      Test.$loadAll({model_id: item.model.id, status: "Completed"}
      ).then ((opts) ->
        for test in opts.objects
          item.avaiable_tests.push({'id': test.id, 'name': test.name})
      ), ((opts) ->
        $scope.setError(opts, 'loading tests')
      )

    $scope.is_form = ->
      $scope.action[0] == 'form'

    $scope.backToForm = () ->
      $scope.toogleAction("form")

    $scope.toogleReport = () ->
      $scope.toogleAction("report", "metrics")

    $scope.toogleAction = (action_name) ->
      report = $scope.report
      csv_ids = ''
      for item in $scope.form_data
        csv_ids += "#{item.model.id},#{item.test.id},"

      $scope.action = [action_name, csv_ids]

    $scope.toogleReportSection = (section) ->
      $scope.section = section

    $scope.generate = ->
      $scope.generating = true
      $scope.generatingProgress = '0%'
      $scope.generatingError = null

      _.defer ->
        $scope.generatingProgress = '70%'
        $scope.$apply()

      $scope.report.$generate()
      .then (->
        $scope.generatingProgress = '100%'
        $scope.generating = false
      ), ((resp) ->
        $scope.generating = false
        $scope.setError(opts, 'generating report')
      )
])
