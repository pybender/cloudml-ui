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
  'XmlImportHandler'

  ($scope, $rootScope, $routeParams, XmlImportHandler) ->
    if not $routeParams.id
      throw new Error "Can't initialize without import handler id"

    $scope.handler = new XmlImportHandler({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.PROCESS_STRATEGIES =
      _.sortBy XmlImportHandler.PROCESS_STRATEGIES, (s)-> s

    $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        extraFields = ['xml_data_sources', 'xml_input_parameters', 'xml_scripts',
                       'entities', 'predict', 'can_edit'].join(',')
        fields = "#{XmlImportHandler.MAIN_FIELDS},#{extraFields}"

      if section[1] == 'xml' then fields = [fields, 'xml'].join(',')

      if fields isnt ''
        $scope.handler.$load
            show: fields
        .then ->
          $scope.LOADED_SECTIONS.push mainSection
          if mainSection is 'dataset'
            $scope.$broadcast('loadDataSet', true)
        , (opts) ->
          $scope.setError(opts, 'loading handler details')

    $scope.initSections($scope.go)
])


.controller('AddXmlImportHandlerCtl', [
  '$scope'
  'XmlImportHandler'

  ($scope, XmlImportHandler) ->
    $scope.types = [{name: 'Db'}, {name: 'Request'}]
    $scope.model = new XmlImportHandler()
])


.controller('PredictCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          #console.log handler, 12
          $scope.predict_models = predict.models
          $scope.predict = predict
          $scope.label = predict.label
          $scope.probability = predict.probability
      )
])
