'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.controller('ModelListCtrl', [
  '$scope'
  '$http'
  '$dialog'
  'settings'
  'Model'

($scope, $http, $dialog, settings, Model) ->
  Model.$loadAll(
    show: 'name,status,created_on,import_params,error'
  ).then ((opts) ->
    $scope.objects = opts.objects
  ), ((opts) ->
    $scope.err = "Error while saving: server responded with " +
        "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). " +
        "Make sure you filled the form correctly. " +
        "Please contact support if the error will not go away."
  )
])

.controller('AddModelCtl', [
  '$scope'
  '$http'
  '$location'
  'settings'
  'Model'

($scope, $http, $location, settings, Model) ->
  $scope.model = new Model()
  $scope.err = ''
  $scope.new = true

  $scope.upload = ->
    $scope.saving = true
    $scope.savingProgress = '0%'
    $scope.savingError = null

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.model.$save().then (->
      $scope.savingProgress = '100%'

      _.delay (->
        $location.path $scope.model.objectUrl()
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

  $scope.setImportHandlerFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.import_handler = element.files[0]
        reader = new FileReader()
        reader.onload = (e) ->
          str = e.target.result
          $scope.model.importhandler = str
          $scope.model.train_importhandler = str
        reader.readAsText($scope.import_handler)

  $scope.setFeaturesFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.features = element.files[0]
        reader = new FileReader()
        reader.onload = (e) ->
          str = e.target.result
          $scope.model.features = str
        reader.readAsText($scope.features)
])

# Upload trained model
.controller('UploadModelCtl', [
  '$scope'
  '$http'
  '$location'
  'settings'
  'Model'

($scope, $http, $location, settings, Model) ->
  $scope.new = true
  $scope.model = new Model()

  $scope.upload = ->
    
    $scope.saving = true
    $scope.savingProgress = '0%'
    $scope.savingError = null
    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()
    $scope.model.$save().then (->
      $scope.savingProgress = '100%'

      _.delay (->
        $location.path $scope.model.objectUrl()
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

  $scope.setModelFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.model_file = element.files[0]
        $scope.model.trainer = element.files[0]

  $scope.setImportHandlerFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.import_handler = element.files[0]
        reader = new FileReader()
        reader.onload = (e) ->
          str = e.target.result
          $scope.model.importhandler = str
        reader.readAsText($scope.import_handler)
])

.controller('ModelDetailsCtrl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  '$dialog'
  'settings'
  'Model'
  'TestResult'
  'Weight'

($scope, $http, $location, $routeParams, $dialog, settings,
  Model, Test, Weight) ->
  DEFAULT_ACTION = 'model:details'
  $scope.action = ($routeParams.action or DEFAULT_ACTION).split ':'
  $scope.$watch 'action', (action) ->
    actionString = action.join(':')
    $location.search(
      if actionString == DEFAULT_ACTION then ""
      else "action=#{actionString}")

    switch action[0]
      when "features" then $scope.go 'features,status'
      when "test" then $scope.goTests()
      when "import_handlers"
        if action[1] == 'train'
          $scope.go 'train_importhandler,status,id'
        else
          $scope.go 'importhandler,status,id'
      else $scope.go 'status,created_on,target_variable,error,
labels,weights_synchronized,example_id,example_label,updated_on,
name'

  if not $scope.model
    if not $routeParams.id
      err = "Can't initialize without model id"
    $scope.model = new Model({_id: $routeParams.id})

  $scope.$watch 'model.status', (status) ->
    if status in ['Queued', 'Training', 'Error', 'New']
      $scope.showLog = true
      $scope.log_messages = []
      params = "channel=trainmodel_log&model=" + $scope.model.name
      log_sse = $scope.getEventSource(params=params)
      handleCallback = (msg) ->
        $scope.$apply(() ->
          if msg?
            data = JSON.parse(msg.data)
            $scope.log_messages.push(data['data']['msg']))
      log_sse.addEventListener('message', handleCallback)

  $scope.toggleAction = (action) =>
    $scope.action = action

  $scope.go = (fields, callback) ->
    $scope.model.$load(
      show: fields
      ).then (->
        $scope.modelLoaded = true
        if callback?
          callback()
      ), (->
        $scope.err = data
      )

  $scope.goTests = () ->
    $scope.go 'name,status,created_on,target_variable,error,labels'
    Test.$loadAll(
      $scope.model._id,
      show: 'name,created_on,status,parameters,accuracy,examples_count'
    ).then ((opts) ->
      $scope.tests = opts.objects
    ), ((opts) ->
      $scope.err = "Error while loading tests: server responded with " +
        "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )

  $scope.saveTrainHandler = =>
    $scope.model.$save(only: ['train_importhandler']).then (() ->
      $scope.msg = 'Import Handler for training model saved'
    ), (() ->
      throw new Error "Unable to save import handler"
    )

  $scope.saveTestHandler = =>
    $scope.model.$save(only: ['importhandler']).then (() ->
      $scope.msg = 'Import Handler for tests saved'
    ), (() ->
      throw new Error "Unable to save import handler"
    )

  $scope.saveModel = =>
    $scope.model.$save(only: ['name',
                              'example_label',
                              'example_id']).then (() ->
      $scope.editMode = false
    ), ((opts) ->
       $scope.err = "Error while saving model details: server responded with " +
        "#{opts.status} " +
        "(#{opts.data.response.error.message or "no message"}). "
    )
    
])

.controller('TrainModelCtrl', [
  '$scope'
  '$http'
  'dialog'
  'settings'

  ($scope, $http, dialog, settings) ->
    $scope.model = dialog.model
    $scope.model.$load(
      show: 'import_params'
      ).then (->
        $scope.params = $scope.model.import_params
      ), (->
        $scope.err = data
      )

    $scope.parameters = {}

    $scope.close = ->
      dialog.close()

    $scope.start = (result) ->
      $scope.model.$train($scope.parameters).then (() ->
        $scope.close()
      ), (() ->
        throw new Error "Unable to start model training"
      )
])

.controller('DeleteModelCtrl', [
  '$scope'
  '$http'
  'dialog'
  'settings'
  '$location'

  ($scope, $http, dialog, settings, location) ->
    $scope.model = dialog.model

    $scope.close = ->
      dialog.close()

    $scope.delete = (result) ->
      $scope.model.$delete().then (() ->
        $scope.close()
        location.path "#/models"
      ), ((opts) ->
        if opts.data
          $scope.err = "Error while deleting model:" +
            "server responded with " + "#{opts.status} " +
            "(#{opts.data.response.error.message or "no message"}). "
        else
          $scope.err = "Error while deleting model"
      )
])

.controller('ModelActionsCtrl', [
  '$scope'
  '$dialog'

  ($scope, $dialog) ->
    $scope.init = (opts={}) =>
      if not opts.model
        throw new Error "Please specify model"

      $scope.model = opts.model

    $scope.test_model = (model)->
      d = $dialog.dialog(
        modalFade: false
      )
      d.model = model
      d.open('partials/modal.html', 'TestDialogController')

    $scope.train_model = (model)->
      d = $dialog.dialog(
        modalFade: false
      )
      d.model = model
      d.open('partials/models/model_train_popup.html',
             'TrainModelCtrl')

    $scope.delete_model = (model)->
      d = $dialog.dialog(
        modalFade: false
      )
      d.model = model
      d.open('partials/models/delete_model_popup.html', 'DeleteModelCtrl')
  
])
