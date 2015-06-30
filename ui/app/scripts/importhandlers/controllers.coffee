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
      template: 'partials/import_handler/load_data.html'
      ctrlName: 'LoadDataDialogCtrl'

  $scope.delete = (handler) ->
    $scope.openDialog $scope,
      model: handler
      template: 'partials/base/delete_dialog.html'
      ctrlName: 'DeleteImportHandlerCtrl'
      action: 'delete import handler'
      path: "/handlers/#{handler.TYPE.toLowerCase()}"

  $scope.testHandler = (handler) ->
    $scope.openDialog $scope,
      template: 'partials/import_handler/test_handler.html'
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
