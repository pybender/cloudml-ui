'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.controller('ModelListCtrl', [
  '$scope'
  '$location'
  'Model'

  ($scope, $location, Model) ->
    $scope.MODEL = Model
    $scope.FIELDS = Model.MAIN_FIELDS + ',tags'
    $scope.ACTION = 'loading models'
    $scope.currentTag = $location.search()['tag']
    $scope.kwargs = {'tag': $scope.currentTag}
])


.controller('TagCloudCtrl', [
  '$scope'
  'Tag'

  ($scope, Tag) ->
    Tag.$loadAll(
      show: 'text,count'
    ).then ((opts) ->
      $scope.tag_list = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading tags list')
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
  'Tag'

  ($scope, $location, $routeParams, Model, Test, Tag) ->
    # Configure Select2 widget for model tags edditing
    # TODO: init data
    $scope.params = {}

    $scope.select2params = {
      multiple: true,
      query: (query) ->
        data = {results: []}
        angular.forEach($scope.tag_list, (item, key) ->
          data.results.push(item)
        )
        query.callback(data)

      createSearchChoice: (term, data) ->
        cmp = () ->
          return this.text.localeCompare(term) == 0
        if $(data).filter(cmp).length == 0 then return {id: term, text: term}
    }

    Tag.$loadAll(
      show: 'text,id'
    ).then ((opts) ->
      $scope.tag_list = []
      for t in opts.objects
        if t.text?
          $scope.tag_list.push {'text': t.text, 'id': t.id}

    ), ((opts) ->
      $scope.setError(opts, 'loading tags')
    )

    if not $routeParams.id
      throw new Error "Can't initialize without model id"
    $scope.model = new Model({_id: $routeParams.id})
    $scope.LOADED_SECTIONS = []

    $scope.load = (fields, section) ->
      $scope.model.$load(
        show: fields
        ).then (->
          $scope.LOADED_SECTIONS.push section
          if $scope.params['tags']?
            $scope.params['tags'] = []
            for t in $scope.model.tags
              $scope.params['tags'].push {'id': t, 'text': t}
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
      if name not in $scope.LOADED_SECTIONS
        extra_fields = ''
        switch name
          when 'model'
            extra_fields = 'created_on,target_variable,
error,labels,weights_synchronized,example_id,example_label,
updated_on,dataset._id,dataset.name,feature_count,test_import_handler.name,
train_import_handler.name,train_import_handler.import_params,tags,
test_import_handler.import_params,train_import_handler._id,
test_import_handler._id'
          when 'features' then extra_fields = 'features'

        if 'main' in $scope.LOADED_SECTIONS
          # Do not need load main fields -> only etra
          if extra_fields != ''
            $scope.load(extra_fields, name)
        else
          $scope.load(extra_fields + ',' + Model.MAIN_FIELDS, name)
          $scope.LOADED_SECTIONS.push 'main'

        if name == 'test' then $scope.goTests()

    $scope.initSections($scope.goSection)

    $scope.updateTags = () ->
      $scope.model.tags = []
      for t in $scope.params['tags']
        $scope.model.tags.push t['text']

      $scope.model.$save(only: ['tags']).then (->), (->
        $scope.setError(opts, 'saving model tags'))
  ])

.controller('BaseModelDataSetActionCtrl', [
  '$scope'
  '$rootScope'

  ($scope, $rootScope) ->
    # DataSet section specific methods
    if $scope.handler?
      $scope.params = $scope.handler.import_params

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
      $scope.dialog.close()
])

.controller('TrainModelCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.dialog = dialog
    $scope.resetError()
    $scope.parameters = {}
    $scope.model = dialog.model
    $scope.handler = $scope.model.train_import_handler_obj

    $scope.start = (result) ->
      model = $scope.dialog.model
      model.$train($scope.parameters).then (() ->
        dialog.close()
      ), ((opts) ->
        $scope.setError(opts, 'starting model training')
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
      $scope._showModelActionDialog(model, 'test', (model) ->
        $scope.openDialog($dialog, model, 'partials/testresults/run_test.html',
                        'TestDialogController', 'modal large'))

    $scope.reload_model = (model)->
      model.$reload()

    $scope.train_model = (model)->
      $scope._showModelActionDialog(model, 'train', (model) ->
        $scope.openDialog($dialog, model,
            'partials/models/model_train_popup.html',
            'TrainModelCtrl', 'modal large'))

    $scope.delete_model = (model) ->
      $scope.openDialog($dialog, model,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete model', 'models')

    $scope._showModelActionDialog = (model, action, fn)->
      if eval('model.' + action + '_import_handler_obj')?
        fn(model)
      else
        model.$load(
          show: action + '_import_handler'
          ).then (->
            fn(model)
          ), (->
            $scope.setError(opts, 'loading import handler details')
          )
])
