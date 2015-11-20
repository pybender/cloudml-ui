'use strict'

angular.module('app.importhandlers.controllers', ['app.config', ])

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

.controller('ImportHandlerSelectCtrl', [
  '$scope'
  '$http'
  'settings'
  'auth'

  ($scope, $http, settings, auth) ->
    $http(
      method: 'GET'
      url: "#{settings.apiUrl}any_importhandlers/"
      headers: _.extend(settings.apiRequestDefaultHeaders, {
        'X-Auth-Token': auth.get_auth_token()})
      params: {show: 'name,type,id'}
    )
    .then ((resp) =>
      data = resp.data.import_handler_for_any_types
      $scope.handlers_list = []
      for h in data
        $scope.handlers_list.push {value: h.id + h.type, text: h.name + '(' + h.type + ')'}
      $scope.handlers_list = _.sortBy $scope.handlers_list, (o) -> o.text
    )
    , (opts) ->
        $scope.setError(opts, 'loading import handler list')
])

.controller('ImportHandlerActionsCtrl', ['$scope', ($scope) ->
  $scope.importData = (handler) ->
    $scope.openDialog $scope,
      model: handler
      template: 'partials/importhandlers/load_data.html'
      ctrlName: 'LoadDataDialogCtrl'

  $scope.delete = (handler) ->
    $scope.openDialog $scope,
      model: handler
      template: 'partials/base/delete_dialog.html'
      ctrlName: 'DeleteImportHandlerCtrl'
      action: 'delete import handler'
      path: "/importhandlers/#{handler.TYPE.toLowerCase()}"

  $scope.testHandler = (handler) ->
    $scope.openDialog $scope,
      template: 'partials/importhandlers/test_handler.html'
      ctrlName: 'ImportTestDialogCtrl'
      action: 'test import handler'
      extra: {handler: $scope.handler}

  $scope.uploadHandlerToPredict = (model) ->
    $scope.openDialog $scope,
      model: model
      template: 'partials/servers/choose.html'
      ctrlName: 'ImportHandlerUploadToServerCtrl'

  $scope.clone = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/importhandlers/xml/clone_popup.html'
        ctrlName: 'CloneXmlImportHandlerCtrl'
        action: 'clone xml import handler'
        path: model.BASE_UI_URL
      })
])

.controller('DeleteImportHandlerCtrl', [
  '$scope'
  '$location'
  'Model'
  'openOptions'

  ($scope, $location, Model, openOptions) ->
    $scope.resetError()
    $scope.MESSAGE = openOptions.action
    $scope.model = openOptions.model
    $scope.path = openOptions.path
    $scope.action = openOptions.action
    $scope.extra_template = 'partials/importhandlers/extra_delete.html'

    $scope.loadModels = () ->
      Model.$by_handler(
        handler: $scope.model.id,
        show: 'name,id,on_s3'
      ).then ((opts) ->
        $scope.umodels = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading models that use import handler')
      )

    $scope.loadModels()
])

.controller('ImportTestDialogCtrl', [
  '$scope'
  'openOptions'
  '$window'

  ($scope, openOptions, $window) ->
    $scope.handler = openOptions.extra.handler
    $scope.params = $scope.handler.import_params
    $scope.parameters = {}
    $scope.test_limit = 2
    $scope.err = ''

    $scope.runTestImport = () ->
      $scope.handler.$getTestImportUrl($scope.parameters, $scope.test_limit
      ).then((resp) ->
        $scope.$close(true)
        $window.location.replace resp.data.url
      , ((opts) ->
        $scope.err = $scope.setError(opts, 'testing import handler')
      ))
])

.controller('ImportHandlerUploadToServerCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'

  ($scope, $rootScope, openOptions) ->
    $scope.resetError()
    $scope.model = openOptions.model
    $scope.model.server = null

    $scope.upload = () ->
      $scope.model.$uploadPredict($scope.model.server)
      .then (resp) ->
        $rootScope.msg = resp.data.status
      , (opts)->
        $rootScope.msg = $scope.setError(opts, 'error uploading to predict')
      $scope.$close(true)
])


.controller('QueryTestDialogCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.handlerUrl = openOptions.extra.handlerUrl
    $scope.datasources = (ds for ds in openOptions.extra.datasources when \
      ds.type is 'sql' or ds.type is 'db')
    $scope.query = openOptions.extra.query
    $scope.params = $scope.query.getParams()

    if !$scope.query.test_params
      $scope.query.test_params = {}
    if !$scope.query.test_limit
      $scope.query.test_limit = 2
    if !$scope.query.test_datasource
      $scope.query.test_datasource = $scope.datasources[0].name

    $scope.runQuery = () ->
      $scope.query.test = {}
      $scope.query.$run($scope.query.test_limit, $scope.query.test_params,
        $scope.query.test_datasource, $scope.handlerUrl
      ).then((resp) ->
        $scope.query.test.columns = resp.data.columns
        $scope.query.test.data = resp.data.data
        $scope.query.test.sql = resp.data.sql
        $scope.$close(true)
      , ((opts) ->
        $scope.query.test.error = $scope.setError(opts, 'testing sql query')
      ))
])
