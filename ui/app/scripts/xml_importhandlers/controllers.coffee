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
    $scope.PROCESS_STRATEGIES = ImportHandler.PROCESS_STRATEGIES

    $scope.codemirrorOptions = {
      mode: 'javascript', readOnly: true, json: true
    }

    $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        fields = ImportHandler.MAIN_FIELDS + ',xml_data_sources,
input_parameters,scripts,entities'
        if mainSection == 'dataset'
          setTimeout(() ->
            $scope.$broadcast('loadDataSet', true)
            $scope.LOADED_SECTIONS.push mainSection
          , 100)

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
