'use strict'

angular.module('app.importhandlers.xml.controllers.importhandlers', ['app.config', ])

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
                       'entities', 'predict', 'can_edit', 'crc32', 'locked'].join(',')
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

    # note: used to saving the file after choosing it.
    # othervise would be setted after changing another field.
    $scope.loadFile = ($fileContent) ->
      $scope.model.data = $fileContent
      alert 1
      $scope.$apply()
])

.controller('CloneXmlImportHandlerCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'
  '$location'
  'XmlImportHandler'

  ($scope, $rootScope, openOptions, $location, XmlImportHandler) ->
    $scope.resetError()
    $scope.handler = openOptions.model

    $scope.clone = (result) ->
      $scope.handler.$clone().then ((opts) ->
        handler = new XmlImportHandler(opts.data.xml_import_handler)
        $scope.$close(true)
        $location.url(handler.objectUrl())
      ), ((opts) ->
        $scope.setError(opts, 'error clonning the xml import handler')
      )
])

# Controller to manage editing xml text of an xml import handler
# Expects:
#     $scope.handler
#     XmlIHXmlForm.ihXml
.controller('XmlIHXmlEditCtrl', [
    '$scope'
    '$route'
    ($scope, $route)->
      $scope.$watch 'handler.xml', (newValue)->
        if not newValue or $scope.handler.originalXml
          return
        $scope.handler.originalXml = newValue
      $scope.resetXmlChanges = ->
        $scope.handler.xml = $scope.handler.originalXml
        $scope.XmlIHXmlForm.ihXml.$setPristine()
      $scope.saveXml = ->
        $scope.handler.$updateXml()
        .then ->
          $route.reload()
        , (opts)->
          $scope.setError(opts, 'saving import handler xml')
  ])
