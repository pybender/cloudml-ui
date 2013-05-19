'use strict'

### Import Handlers specific Controllers ###

angular.module('app.importhandlers.controllers', ['app.config', ])

.controller('ImportHandlerListCtrl', [
  '$scope'
  '$http'
  '$dialog'
  'settings'
  'ImportHandler'

($scope, $http, $dialog, settings, ImportHandler) ->
  ImportHandler.$loadAll(
    show: 'name,type,created_on,updated_on'
  ).then ((opts) ->
    $scope.objects = opts.objects
  ), ((opts) ->
    $scope.err = "Error while saving: server responded with " +
        "#{resp.status} " +
        "(#{resp.data.response.error.message or "no message"}). " +
        "Make sure you filled the form correctly. " +
        "Please contact support if the error will not go away."
  )
])

.controller('ImportHandlerDetailsCtrl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  '$dialog'
  'settings'
  'ImportHandler'

($scope, $http, $location, $routeParams, $dialog, settings, ImportHandler) ->
  if not $routeParams.id
    err = "Can't initialize without import handler id"
  $scope.handler = new ImportHandler({_id: $routeParams.id})

  $scope.handler.$load(
    show: 'name,type,created_on,updated_on,data'
    ).then (->
      loaded_var = true
      if callback?
        callback()
    ), (->
      $scope.err = data
    )
])

.controller('AddImportHandlerCtl', [
  '$scope'
  '$http'
  '$location'
  'settings'
  'ImportHandler'

($scope, $http, $location, settings, ImportHandler) ->
  $scope.handler = new ImportHandler()
  $scope.types = [{name: 'Db'}, {name: 'Request'}]
  $scope.err = ''
  $scope.new = true

  $scope.add = ->
    $scope.saving = true
    $scope.savingProgress = '0%'
    $scope.savingError = null

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.handler.$save().then (->
      $scope.savingProgress = '100%'

      _.delay (->
        $location.path $scope.handler.objectUrl()
        $scope.$apply()
      ), 300

    ), ((resp) ->
      $scope.saving = false
      $scope.err = "Error while saving: server responded with " +
        "#{resp.status} " +
        "(#{resp.data.response.error.message or "no message"}). " +
        "Make sure you filled the form correctly. " +
        "Please contact support if the error will not go away."
    )

  $scope.setDataFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.data = element.files[0]
        reader = new FileReader()
        reader.onload = (e) ->
          str = e.target.result
          $scope.handler.data = str
        reader.readAsText($scope.data)
])