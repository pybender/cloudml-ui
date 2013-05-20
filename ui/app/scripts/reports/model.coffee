angular.module('app.reports.model', ['app.config'])

.factory('CompareReport', [
  '$http'
  '$q'
  'settings'
  'Model'
  'TestResult'
  'Data'
  'BaseModel'
  
  ($http, $q, settings, Model, Test, Data, BaseModel) ->
    class CompareReport extends BaseModel
      generated: false
      API_FIELDNAME: 'data'

      constructor: (data) ->
        @data = data

      loadFromJSON: (origData) =>
        @data = origData
        @rocCurves = {}
        @precisionRecallCurves = {}
        for item in @data
          test = new Test(item['test'])
          item['test'] = test
          auc = test.metrics.roc_auc.toFixed(4)
          @rocCurves[test.fullName() + " (AUC = " + auc + ")"] =
            test.metrics.roc_curve

          @precisionRecallCurves[test.fullName()] =
            test.metrics.precision_recall_curve.reverse()

      $generate: =>
        opts = {}
        i = 1
        for item in @data
          opts['model' + i] = item['model']["_id"]
          opts['test' + i] = item['test']["_id"]
          i += 1

        @$make_request(settings.apiUrl + "reports/compare/", opts)

    return CompareReport
])