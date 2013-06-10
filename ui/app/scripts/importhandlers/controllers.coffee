'use strict'

### Import Handlers specific Controllers ###

angular.module('app.importhandlers.controllers', ['app.config', ])

.controller('ImportHandlerListCtrl', [
  '$scope'
  '$dialog'
  'ImportHandler'

($scope, $dialog, ImportHandler) ->
  ImportHandler.$loadAll(
    show: 'name,type,created_on,updated_on,import_params'
  ).then ((opts) ->
    $scope.objects = opts.objects
  ), ((opts) ->
    $scope.setError(opts, 'loading handler list')
  )
])

.controller('ImportHandlerDetailsCtrl', [
  '$scope'
  '$routeParams'
  'ImportHandler'
  'DataSet'
  '$dialog'

  ($scope, $routeParams, ImportHandler, DataSet, $dialog) ->
    if not $routeParams.id
      err = "Can't initialize without import handler id"
    $scope.handler = new ImportHandler({_id: $routeParams.id})

    $scope.go = (section) ->
      $scope.loadDetails()
      switch section[0]
        when "dataset" then $scope.loadDataSets()

    $scope.loadDetails = () ->
      $scope.handler.$load(
        show: 'name,type,created_on,updated_on,data,import_params'
      ).then (->), ((opts) ->
        $scope.setError(opts, 'loading handler details')
      )

    $scope.delete_dataset = (dataset)->
      $scope.openDialog(dataset, 'partials/datasets/delete_dataset_popup.html',
                        'DeleteDatasetCtrl')

    $scope.openDialog = (dataset, templete, ctrlName, cssClass='modal large') ->
      d = $dialog.dialog(
        modalFade: false,
        dialogClass: cssClass
      )
      d.dataset = dataset
      d.open(templete, ctrlName)

    $scope.loadDataSets = () ->
      DataSet.$loadAll(
        $scope.handler._id,
        show: 'name,created_on,status,error,data,import_params,
import_handler_id'
      ).then ((opts) ->
        $scope.datasets = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading datasets')
      )

    $scope.saveData = () ->
      $scope.handler.$save(only: ['data'])
      .then (->), ((opts) ->
        $scope.setError(opts, 'saving handler details')
      )

    $scope.initSections($scope.go)
    $scope.initLogMessages("channel=importdata_log&model=" + $scope.handler._id)
])

.controller('DeleteDatasetCtrl', [
  '$scope'
  'dialog'
  '$location'

  ($scope, dialog, $location) ->
    $scope.dataset = dialog.dataset
    $scope.resetError()

    $scope.close = ->
      dialog.close()

    $scope.delete = (result) ->
      $scope.dataset.$delete().then (() ->
        $scope.close()
        $location.path "/importhandlers/#{$scope.dataset.import_handler_id}"
      ), ((opts) ->
        $scope.setError(opts, 'deleting dataset')
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

    ), ((opts) ->
      $scope.setError(opts, 'adding import handler')
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


.controller('LoadDataDialogCtrl', [
  '$scope'
  '$location'
  'dialog'
  'ImportHandler'
  'DataSet'

  ($scope, $location, dialog, ImportHandler, DataSet) ->
    $scope.parameters = {}
    $scope.handler = dialog.handler
    $scope.handler.$load(show: 'import_params').then (->
      $scope.params = $scope.handler.import_params
    ), ((opts)->
      $scope.setError(opts, 'loading handler parameters')
    )

    $scope.close = ->
      dialog.close()

    $scope.start = (result) ->
      $scope.dataset = new DataSet({'import_handler_id': $scope.handler._id})
      $scope.dataset.$save($scope.parameters).then (() ->
        $scope.close()
        url = $scope.handler.objectUrl()
        $location.path(url).search({'action': 'dataset:list',
        'a': Math.random()})
      ), ((opts) ->
        $scope.setError(opts, 'creating dataset')
      )
])

.controller('ImportHandlerActionsCtrl', [
  '$scope'
  '$dialog'
($scope, $dialog) ->
  $scope.importData = (handler) ->
    d = $dialog.dialog(modalFade: false)
    d.handler = handler
    d.open('partials/import_handler/load_data.html', 'LoadDataDialogCtrl')

])

.controller('ImportHandlerSelectCtrl', [
  '$scope'
  'ImportHandler'

  ($scope, ImportHandler) ->
    ImportHandler.$loadAll(
      show: 'name'
    ).then ((opts) ->
      $scope.handlers = opts.objects
      $scope.handlers_list  = []
      for h in $scope.handlers
        $scope.handlers_list.push {value: h._id, text: h.name}

    ), ((opts) ->
      $scope.setError(opts, 'loading import handler list')
    )
])