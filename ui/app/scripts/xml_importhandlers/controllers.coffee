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

.controller('BigListCtrl', [
  '$scope'
  '$location'

  ($scope, $location) ->
    $scope.currentTag = $location.search()['tag']
    $scope.kwargs = {
      tag: $scope.currentTag
      per_page: 5
      sort_by: 'updated_on'
      order: 'desc'
    }
    $scope.page = 1

    $scope.init = (updatedByMe, listUniqueName) ->
      $scope.listUniqueName = listUniqueName
      if updatedByMe
        $scope.$watch('user', (user, oldVal, scope) ->
          if user?
            $scope.filter_opts = {
              'updated_by_id': user.id
              'status': ''}
            $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
              $scope.$emit 'BaseListCtrl:start:load', listUniqueName
            , true)
        , true)
      else
        $scope.filter_opts = {'status': ''}

    $scope.showMore = () ->
      $scope.page += 1
      extra = {'page': $scope.page}
      $scope.$emit 'BaseListCtrl:start:load', $scope.listUniqueName, true, extra
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
