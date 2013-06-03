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
  'Weight'

  ($scope, $location, $routeParams, Model, Test, Weight) ->
    if not $scope.model
      if not $routeParams.id
        throw new Error "Can't initialize without model id"
      $scope.model = new Model({_id: $routeParams.id})
    $scope.person_name = "John Doe"
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

    $scope.load = (fields) ->
      $scope.model.$load(
        show: fields
        ).then (->
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
    
    $scope.goSection = (section) ->
      name = section[0]
      switch name
        when 'model' then fields = 'status,created_on,target_variable,
error, labels,weights_synchronized,example_id,example_label,
updated_on,name,test_import_handler.name,test_import_handler._id,
train_import_handler.name,train_import_handler._id'
        when 'features' then fields = 'name,status,features'
        else fields = 'name,status'
      $scope.load fields
      if name == 'log'
        $scope.initLog()

    $scope.initSections($scope.goSection)
  ])

.controller('TrainModelCtrl', [
  '$scope'
  'dialog'
  'AwsInstance'

  ($scope, dialog, AwsInstance) ->
    $scope.parameters = {}
    $scope.model = dialog.model
    $scope.model.$load(
      show: 'import_params'
      ).then (->
        $scope.params = $scope.model.import_params
      ), ((opts)->
        $scope.setError(opts, 'loading model details')
      )

    AwsInstance.$loadAll(
      show: 'name,type,ip,is_default'
    ).then ((opts) ->
      $scope.aws_instances = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading aws instances')
    )

    $scope.close = ->
      dialog.close()

    $scope.start = (result) ->
      $scope.model.$train($scope.parameters).then (() ->
        $scope.close()
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

    $scope.openDialog = (model, templete, ctrl_name) ->
      d = $dialog.dialog(
        modalFade: false
      )
      d.model = model
      d.open(templete, ctrl_name)
])
