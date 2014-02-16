'use strict'

### Trained Model specific Controllers ###

FIELDS_BY_SECTION = {
  'model': 'classifier,features_set_id'
  'training': 'error,weights_synchronized,memory_usage,
trained_by,trained_on,training_time,datasets,train_records_count,trainer_size'
  'about': 'created_on,target_variable,example_id,example_label,
labels,updated_on,feature_count,test_import_handler,
train_import_handler,created_by,data_fields,test_handler_fields,tags'
  'main': 'name,status'
}

angular.module('app.models.controllers', ['app.config', ])


.controller('TagCtrl', [
  '$scope'
  '$location'

  ($scope, $location) ->
    $scope.currentTag = $location.search()['tag']
])

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
    $scope.kwargs = {
      tag: $scope.currentTag
      per_page: 5
      sort_by: 'updated_on'
      order: 'desc'
    }
    $scope.page = 1
    $scope.STATUSES = ['', 'New', 'Queued', 'Importing',
    'Imported', 'Requesting Instance', 'Instance Started',
    'Training', 'Trained', 'Error', 'Canceled']

    $scope.init = (updatedByMe, modelName) ->
      $scope.modelName = modelName
      if updatedByMe
        $scope.$watch('user', (user, oldVal, scope) ->
          if user?
            $scope.filter_opts = {
              'updated_by_id': user.id
              'status': ''}
            $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
              $scope.$emit 'BaseListCtrl:start:load', modelName
            , true)
        , true)
      else
        $scope.filter_opts = {'status': ''}

    $scope.showMore = () ->
      $scope.page += 1
      extra = {'page': $scope.page}
      $scope.$emit('BaseListCtrl:start:load',
        $scope.modelName, true, extra)
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
    $scope.formats = [
      {name: 'JSON', value: 'json'}, {name: 'CSV', value: 'csv'}
    ]
    $scope.model = new Model({train_format: 'json', test_format: 'json'})
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
    if not $routeParams.id
      throw new Error "Can't initialize without model id"

    $scope.model = new Model({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.params = {'tags': []}

    $scope.load = (fields, section) ->
      if !fields then return

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

    $scope.goSection = (section) ->
      name = section[0]
      subsection = section[1]
      if name == 'test'
        setTimeout(() ->
          $scope.$broadcast('loadTest', true)
          $scope.LOADED_SECTIONS.push name
        , 100)
      if name == 'model' && subsection == 'json'
        $scope.load('features', name + subsection)

      fields = ''
      if 'main' not in $scope.LOADED_SECTIONS
        fields = FIELDS_BY_SECTION['main']
        $scope.LOADED_SECTIONS.push 'main'

      if name not in $scope.LOADED_SECTIONS
        if FIELDS_BY_SECTION[name]?
          fields += ',' + FIELDS_BY_SECTION[name]

      $scope.load(fields, name)

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

    $scope.codemirrorOptions = {
      mode: 'javascript', readOnly: true, json: true
    }

    $scope.updateTags = () ->
      $scope.model.tags = []
      for t in $scope.params['tags']
        $scope.model.tags.push t['text']

      $scope.model.$save(only: ['tags']).then (->), (->
        $scope.setError(opts, 'saving model tags'))

    $scope.initSections($scope.goSection)
  ])


.controller('BaseModelDataSetActionCtrl', [
  '$scope'
  '$rootScope'

  ($scope, $rootScope) ->
    $scope.data.format = 'json'
    $scope.data.new_dataset_selected = 0
    $scope.data.existing_instance_selected = 1

    $scope.formats = [
      {name: 'JSON', value: 'json'}, {name: 'CSV', value: 'csv'}
    ]

    $scope.initForm = () ->
      # Form elements initialization
      # dataset section
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

    $scope.close = ->
      $scope.dialog.close()
      $scope.resetError()
])

.controller('TrainModelCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.dialog = dialog
    $scope.resetError()
    $scope.model = dialog.model
    $scope.data = {}

    $scope.handler = $scope.model.train_import_handler_obj
    $scope.multiple_dataset = true

    $scope.start = (result) ->
      dialog.model.$train($scope.data).then (() ->
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
        model.$load(show: 'test_handler_fields').then (->
          $scope.openDialog($dialog, model,
            'partials/testresults/run_test.html',
            'TestDialogController', 'modal large'))
        )

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

    $scope.editClassifier = (model) ->
      $scope.openDialog($dialog, null,
        'partials/features/classifiers/edit.html',
          'ModelWithParamsEditDialogCtrl',
        'modal', 'edit classifier', 'classifiers',
        {model: model, fieldname: 'classifier'}
      )

    $scope._showModelActionDialog = (model, action, fn)->
      if eval('model.' + action + '_import_handler_obj')?
        fn(model)
      else
        model.$load(
          show: action + '_import_handler'
          ).then (->
            fn(model)
          ), ((opts) ->
            $scope.setError(opts, 'loading import handler details')
          )
])
