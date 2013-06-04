'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.controller('ModelListCtrl', [
  '$scope'
  'Model'

  ($scope, Model) ->
    Model.$loadAll(
      show: 'name,status,created_on,import_params,error'
    ).then ((opts) ->
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading models')
    )
])

# Add new model controller
.controller('AddModelCtl', [
  '$scope'
  'Model'

($scope, Model) ->
  $scope.model = new Model()
])

# Upload trained model controller
.controller('UploadModelCtl', [
  '$scope'
  'Model'

  ($scope, Model) ->
    $scope.model = new Model()

    $scope.setModelFile = (element) ->
      $scope.$apply ($scope) ->
        $scope.model.trainer = element.files[0]
])

.controller('ModelDetailsCtrl', [
  '$scope'
  '$location'
  '$routeParams'
  'Model'
  'TestResult'

  ($scope, $location, $routeParams, Model, Test) ->
    if not $routeParams.id
      throw new Error "Can't initialize without model id"
    $scope.model = new Model({_id: $routeParams.id})
    $scope.LOADED_SECTIONS = []

    $scope.initLog = () ->
      $scope.log_messages = []
      params = "channel=trainmodel_log&model=" + $scope.model._id
      log_sse = $scope.getEventSource(params=params)
      handleCallback = (msg) ->
        $scope.$apply(() ->
          if msg?
            data = JSON.parse(msg.data)
            $scope.log_messages.push(data['data']['msg']))
      log_sse.addEventListener('message', handleCallback)

    $scope.initLog()

    $scope.load = (fields, section) ->
      $scope.model.$load(
        show: fields
        ).then (->
          $scope.LOADED_SECTIONS.push section
        ), (->
          $scope.setError(opts, 'loading model details')
        )

    $scope.goTests = () ->
      Test.$loadAll(
        $scope.model._id,
        show: 'name,created_on,status,parameters,accuracy,examples_count'
      ).then ((opts) ->
        $scope.tests = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading tests')
      )

    MAIN_FIELDS = ',name,_id,status,train_import_handler._id,
train_import_handler.import_params,train_import_handler.name'

    $scope.goSection = (section) ->
      name = section[0]
      if name not in $scope.LOADED_SECTIONS
        extra_fields = ''
        switch name
          when 'model' then extra_fields = 'created_on,target_variable,
  error,labels,weights_synchronized,example_id,example_label,
  updated_on,test_import_handler.name,test_import_handler._id'
          when 'features' then extra_fields = 'features'

        if 'main' in $scope.LOADED_SECTIONS
          # Do not need load main fields -> only etra
          if extra_fields != ''
            $scope.load(extra_fields, name)
        else
          $scope.load(extra_fields + MAIN_FIELDS, name)
          $scope.LOADED_SECTIONS.push 'main'

    $scope.initSections($scope.goSection)
    $scope.$on('modelUpdated', (model) ->
      $scope.load(MAIN_FIELDS)
    )
  ])

.controller('TrainModelCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.parameters = {}
    $scope.model = dialog.model
    $scope.handler = $scope.model.train_import_handler_obj
    if $scope.handler?
      $scope.params = $scope.handler.import_params

    $scope.changeDataSet = ->
      $scope.existed = $scope.parameters["dataset"]

    $scope.changeParams = (param) ->
      $scope.paramsFilled = true
      $scope.new = false
      for key in $scope.params
        val = $scope.parameters[key]
        if val?
          $scope.new = true
        else
          $scope.paramsFilled = false
      return

    $scope.close = ->
      dialog.close()

    $scope.start = (result) ->
      model = $scope.model
      $scope.model.$train($scope.parameters).then (() ->
        $scope.close()
        $rootScope.$broadcast('modelUpdated', model)
      ), ((opts) ->
        $scope.setError(opts, 'starting model training')
      )
])

.controller('DeleteModelCtrl', [
  '$scope'
  'dialog'
  '$location'

  ($scope, dialog, $location) ->
    $scope.model = dialog.model

    $scope.close = ->
      dialog.close()

    $scope.delete = (result) ->
      $scope.model.$delete().then (() ->
        $scope.close()
        $location.path "#/models"
      ), ((opts) ->
        $scope.setError(opts, 'deleting model')
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
      $scope.openDialog(model, 'partials/testresults/run_test.html',
                        'TestDialogController')

    $scope.reload_model = (model)->
      model.$reload()

    $scope.train_model = (model)->
      $scope.openDialog(model, 'partials/models/model_train_popup.html',
                        'TrainModelCtrl')

    $scope.delete_model = (model)->
      $scope.openDialog(model, 'partials/models/delete_model_popup.html',
                        'DeleteModelCtrl')

    $scope.openDialog = (model, templete, ctrlName, cssClass='modal large') ->
      d = $dialog.dialog(
        modalFade: false,
        dialogClass: cssClass
      )
      d.model = model
      d.open(templete, ctrlName)
])
