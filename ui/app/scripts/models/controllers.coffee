'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.controller('ModelListCtrl', [
  '$scope'
  '$location'
  'Model'

  ($scope, $location, Model) ->
    $scope.MODEL = Model
    $scope.FIELDS = Model.MAIN_FIELDS + ',tags,created_on,created_by,
updated_on,updated_by,comparable,test_handler_fields'
    $scope.ACTION = 'loading models'
    $scope.currentTag = $location.search()['tag']
    $scope.kwargs = {'tag': $scope.currentTag}
    $scope.STATUSES = ['', 'New', 'Queued', 'Importing',
    'Imported', 'Requesting Instance', 'Instance Started',
    'Training', 'Trained', 'Error', 'Canceled']
    $scope.filter_opts = {}
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
        ), ((opts)->
          $scope.setError(opts, 'loading model details')
        )

    $scope.goTests = () ->
      setTimeout(() ->
          $scope.$broadcast('loadTest', true)
          $scope.LOADED_SECTIONS.push 'test'
        , 100)
#      Test.$loadAll(
#        $scope.model._id,
#        show: 'name,created_on,status,parameters,accuracy,examples_count,
#created_by'
#      ).then ((opts) ->
#        $scope.tests = opts.objects
#      ), ((opts) ->
#        $scope.setError(opts, 'loading tests')
#      )

    $scope.goSection = (section) ->
      name = section[0]
      if name not in $scope.LOADED_SECTIONS
        extra_fields = ''
        switch name
          when 'model'
            extra_fields = 'created_on,target_variable,
error,labels,weights_synchronized,example_id,example_label,
updated_on,feature_count,test_import_handler.name,
train_import_handler.name,train_import_handler.import_params,tags,
test_import_handler.import_params,train_import_handler._id,
test_import_handler._id,memory_usage,created_by,trained_by,datasets,data_fields,
train_records_count,test_handler_fields,training_time'
          when 'features' then extra_fields = 'features'

        if 'main' in $scope.LOADED_SECTIONS
          # Do not need load main fields -> only extra
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
    $scope.initForm = () ->
      # Form elements initialization
      # dataset section
      $scope.NEW_DATASET = 'New DataSet'
      params = {}
      $scope.formValid = false
      for p in $scope.params
        params[p] = false
      $scope.formElements[$scope.NEW_DATASET] = params

      $scope.EXISTED_DATASET = 'Existing DataSet'
      $scope.formElements[$scope.EXISTED_DATASET] = {'dataset': false}

      # instance section
      $scope.REQUEST_SPOT_INSTANCE = 'Request Spot Instance'
      $scope.formElements[$scope.REQUEST_SPOT_INSTANCE] = \
      {'spot_instance_type': false}

      $scope.EXISTED_INSTANCE = 'Existing Instance'
      $scope.formElements[$scope.EXISTED_INSTANCE] = {'aws_instance': false}

      if $scope.multiple_dataset
        $scope.select2Options = {
          allowClear: true,
          placeholder: 'Please select dataset or several',
          width: 230  # TODO: better move to template?
        }
      else
        $scope.select2Options = {allowClear: true}

    if $scope.handler?
      $scope.params = $scope.handler.import_params
      $scope.initForm()

    $scope.changeFormData = (column, param) ->
      $scope.formValid = $scope.isDataSetDataValid()

    $scope.activateSectionColumn = (section, name) ->
      $scope.currentColumns[section] = name
      $scope.formValid = $scope.isDataSetDataValid()

    $scope.isDataSetDataValid = () ->
      for section, tab of $scope.currentColumns
        for key, val of $scope.formElements[tab]
          if !val then return false
      return true

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
    $scope.model = dialog.model
    $scope.handler = $scope.model.train_import_handler_obj
    $scope.multiple_dataset = true

    # Form elements for each tab in the section with values
    $scope.formElements = {}
    # Columns by section
    $scope.currentColumns = {'dataset': null, 'instance': null}

    $scope.start = (result) ->
      data = $scope.getData()
      dialog.model.$train(data).then (() ->
        dialog.close()
      ), ((opts) ->
        $scope.setError(opts, 'starting model training')
      )

    # TODO: Remove code duplication
    $scope.getData = () ->
      data = {}
      for section, tab of $scope.currentColumns
        for key, val of $scope.formElements[tab]
          if val then data[key] = val
      return data
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
        model.$load(show: 'test_handler_fields').then (->
          $scope.openDialog($dialog, model,
            'partials/testresults/run_test.html',
            'TestDialogController', 'modal large'))
        )

    $scope.reload_model = (model)->
      model.$reload()

    $scope.cancel_request_spot_instance = (model)->
      model.$cancel_request_spot_instance()

    $scope.train_model = (model)->
      $scope._showModelActionDialog(model, 'train', (model) ->
        $scope.openDialog($dialog, model,
            'partials/models/model_train_popup.html',
            'TrainModelCtrl', 'modal'))

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
