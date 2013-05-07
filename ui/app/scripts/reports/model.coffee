angular.module('app.reports.model', ['app.config'])

.factory('CompareReport', [
  '$http'
  '$q'
  'settings'
  'Model'
  'TestResult'
  'Data'
  
  ($http, $q, settings, Model, Test, Data) ->
    class CompareReport

      constructor: (opts) ->
        @loadFromJSON opts

      generated: false

      ### API methods ###
      objectUrl: =>
        if @model?
          return '/models/' + @model.name + "/tests/" + @name

      # Sets attributes from object received e.g. from API response
      loadFromJSON: (origData) =>
        data = _.extend {}, origData
        _.extend @, data

      $getReportData: =>
        # TODO: any count of tests to compare
        params = {'test1': @test_name1, 'test2': @test_name2,
        'model1': @model_name1, 'model2': @model_name2}
        $http(
          method: 'GET'
          url: settings.apiUrl + "reports/compare"
          headers: {'X-Requested-With': null}
          params: params
        ).then ((resp) =>
          @generated = true
          @tests = []
          @rocCurves = {}
          @precisionRecallCurves = {}
          for key, value of resp.data
            # Adding different count of tests to compare
            if key.indexOf('test') == 0
              test = new Test(resp.data[key])
              @tests.push(test)
              eval("_this." + key + "=test")
              auc = test.metrics.roc_auc.toFixed(4)
              @rocCurves[test.fullName() + " (AUC = " + auc + ")"] =
              test.metrics.roc_curve
              @precisionRecallCurves[test.fullName()] =
              test.metrics.precision_recall_curve.reverse()

            # Adding test examples
            if key.indexOf('examples') == 0
              num = key.replace('examples', '')
              examples = []
              examples_data = resp.data[key]
              for example in examples_data
                examples.push new Data(example)
              eval("_this.test" + num + ".examples=examples")
          return resp

        ), ((resp) =>
          return resp
        )

    return CompareReport
])