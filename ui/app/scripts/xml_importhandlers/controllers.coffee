'use strict'

angular.module('app.xml_importhandlers.controllers', ['app.config', ])

.controller('XmlImportHandlerListCtrl', [
  '$scope'
  '$rootScope'
  'XmlImportHandler'

  ($scope, $rootScope, XmlImportHandler) ->
    $scope.MODEL = XmlImportHandler
    $scope.FIELDS = XmlImportHandler.MAIN_FIELDS
    $scope.ACTION = 'loading handler list'
])

.controller('XmlImportHandlerDetailsCtrl', [
  '$scope'
  '$rootScope'
  '$routeParams'
  '$dialog'
  'XmlImportHandler'

  ($scope, $rootScope, $routeParams, $dialog, ImportHandler) ->
    if not $routeParams.id
      err = "Can't initialize without import handler id"

    $scope.handler = new ImportHandler({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.PROCESS_STRATEGIES =
      _.sortBy ImportHandler.PROCESS_STRATEGIES, (s)-> s

    $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        fields = ImportHandler.MAIN_FIELDS + ',xml_data_sources,
xml_input_parameters,xml_scripts,entities,import_params,predict'
        if mainSection == 'dataset'
          setTimeout(() ->
            $scope.$broadcast('loadDataSet', true)
            $scope.LOADED_SECTIONS.push mainSection
          , 100)

      if section[1] == 'xml' then fields = 'xml'

      if fields != ''
        $scope.handler.$load(
            show: fields
        ).then (->
          $scope.LOADED_SECTIONS.push mainSection
        ), ((opts) ->
          $scope.setError(opts, 'loading handler details')
        )

    $scope.initSections($scope.go)
])


.controller('AddXmlImportHandlerCtl', [
  '$scope'
  'XmlImportHandler'

  ($scope, ImportHandler) ->
    $scope.types = [{name: 'Db'}, {name: 'Request'}]
    $scope.model = new ImportHandler()
])


.controller('PredictCtrl', [
  '$scope'
  'XmlImportHandler'

  ($scope, ImportHandler) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          console.log handler, 12
          $scope.predict_models = predict.models
          $scope.predict = predict
          $scope.label = predict.label
          $scope.probability = predict.probability
      )
])



.controller('XmlQueryTestDialogCtrl', [
    '$scope'
    'dialog'

    ($scope, dialog) ->
      $scope.handler = dialog.extra.handler
      $scope.query = dialog.extra.query
      $scope.params = $scope.query.getParams()
      $scope.dialog = dialog

      if !$scope.query.test_params
        $scope.query.test_params = {}
      if !$scope.query.test_limit
        $scope.query.test_limit = 2
      if !$scope.query.test_datasource
        $scope.query.test_datasource = $scope.handler.xml_data_sources[0].name

      $scope.runQuery = () ->
        $scope.query.test = {}
        $scope.query.$run($scope.query.test_limit, $scope.query.test_params
        ).then((resp) ->
          $scope.query.test.columns = resp.data.columns
          $scope.query.test.data = resp.data.data
          $scope.query.test.sql = resp.data.sql
          dialog.close()
        , ((opts) ->
            $scope.query.test.error = $scope.setError(opts, 'testing sql query')
          ))
  ])
