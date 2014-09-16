'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.constant('MODEL_FIELDS',
  [ 'name','status','test_import_handler', 'train_import_handler',
    'train_import_handler_type', 'test_import_handler_type',
    'test_handler_fields', 'labels'].join(',')
)

.factory('FIELDS_BY_SECTION', [
  'MODEL_FIELDS'

  (MODEL_FIELDS) ->
    model: ['classifier','features_set_id','segments'].join(',')
    training: [
      'error','weights_synchronized','memory_usage','segments', 'trained_by',
      'trained_on','training_time','datasets', 'train_records_count',
      'trainer_size'
    ].join(',')
    about: [
      'created_on','target_variable','example_id','example_label',
      'updated_on','feature_count','created_by','data_fields',
      'test_handler_fields','tags'
    ].join(',')
    main: MODEL_FIELDS
])

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
  'MODEL_FIELDS'

  ($scope, $location, Model, MODEL_FIELDS) ->
    $scope.MODEL = Model
    $scope.FIELDS = MODEL_FIELDS + ',' + ['tags','created_on','created_by',
                                          'updated_on','updated_by',
                                          'comparable'].join(',')
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
      $scope.$emit 'BaseListCtrl:start:load', $scope.modelName, true, extra
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
  'FIELDS_BY_SECTION'
  '$q'

  ($scope, $location, $routeParams, Model, Test, Tag, FIELDS_BY_SECTION, $q) ->
    if not $routeParams.id
      throw new Error "Can't initialize without model id"

    $scope.model = new Model({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.params = {'tags': []}

    $scope.load = (fields, section) ->
      deferred = $q.defer()

      if not fields
        deferred.reject 'empty fields'
        return deferred.promise

      $scope.model.$load(
        show: fields
        ).then (->
          if $scope.params['tags']?
            $scope.params['tags'] = []
            for t in $scope.model.tags
              $scope.params['tags'].push {'id': t, 'text': t}
            if $scope.model.status is 'Trained'
              $scope.model.$getTrainS3Url()
              .then (resp)->
                $scope.model.trainer_s3_url = resp.data.url
              , (opts)->
                $scope.setError(opts, 'loading trainer s3 url')
          $scope.LOADED_SECTIONS.push section
          deferred.resolve 'model loaded'
        ), ((opts)->
          $scope.setError(opts, 'loading model details')
          deferred.reject 'error loading model details'
        )
      return deferred.promise

    $scope.goSection = (section) ->
      name = section[0]
      subsection = section[1]

      # TODO: nader20140907 we need to manually test reloading, I am disabling
      # it for now until I get a chance to test it. The unit test in modesl/controllers.coffee
      # it  'should load features', having the expectations disabled for now
      #if name in $scope.LOADED_SECTIONS
      #  return

      loadedSections = []
      if name == 'model' && subsection == 'json'
        $scope.load('features', name + subsection)

      fields = ''
      if 'main' not in $scope.LOADED_SECTIONS
        loadedSections.push 'main'
        fields = FIELDS_BY_SECTION['main']

      if name not in $scope.LOADED_SECTIONS
        loadedSections.push name
        if FIELDS_BY_SECTION[name]?
          fields += ',' + FIELDS_BY_SECTION[name]

      $scope.load(fields, name).then ->
        for name in loadedSections
          if name not in $scope.LOADED_SECTIONS
            $scope.LOADED_SECTIONS.push name
        if 'test' in loadedSections
          $scope.$broadcast('loadTest', true)

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

    $scope.updateTags = () ->
      $scope.model.tags = []
      for t in $scope.params['tags']
        $scope.model.tags.push t['text']

      $scope.model.$save(only: ['tags'])
      .then (->), (opts)->
        $scope.setError opts, 'saving model tags'

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
      $scope.$close(true)
      $scope.resetError()
])

.controller('TrainModelCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'

  ($scope, $rootScope, openOptions) ->
    $scope.resetError()
    $scope.model = openOptions.model
    $scope.data = {}

    $scope.handler = $scope.model.train_import_handler_obj
    $scope.multiple_dataset = true

    $scope.start = (result) ->
      openOptions.model.$train($scope.data).then (() ->
        $scope.$close(true)
      ), ((opts) ->
        $scope.setError(opts, 'error starting model training')
      )
])

.controller('ModelActionsCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (opts) ->
      if not opts or not opts.model
        throw new Error "Please specify model"

      $scope.model = opts.model

    $scope.test_model = (model)->
      $scope._showModelActionDialog(model, 'test', (model) ->
        model.$load(show: 'test_handler_fields').then (->
          $scope.openDialog({
            model: model
            template: 'partials/testresults/run_test.html'
            ctrlName: 'TestDialogController'
            cssClass: 'modal large'
          }))
        )

    $scope.cancel_request_spot_instance = (model)->
      model.$cancel_request_spot_instance()

    $scope.train_model = (model)->
      $scope._showModelActionDialog(model, 'train', (model) ->
        $scope.openDialog({
          model: model
          template: 'partials/models/model_train_popup.html'
          ctrlName: 'TrainModelCtrl'
        }))

    $scope.delete_model = (model) ->
      $scope.openDialog({
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete model'
      })

    $scope.editClassifier = (model) ->
      $scope.openDialog({
        model: null
        template: 'partials/features/classifiers/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit classifier'
        extra: {model: model, fieldname: 'classifier'}
      })

    $scope.uploadModelToPredict = (model) ->
      $scope.openDialog({
        model: model
        template: 'partials/servers/choose.html'
        ctrlName: 'ModelUploadToServerCtrl'
      })

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

.controller('ModelUploadToServerCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'

  ($scope, $rootScope, openOptions) ->
    $scope.resetError()
    $scope.model = openOptions.model
    $scope.model.server = null

    $scope.upload = () ->
      $scope.model.$uploadPredict($scope.model.server).then((resp) ->
        $rootScope.msg = resp.data.status
      )
      $scope.$close(true)
])

.controller('ModelDataSetDownloadCtrl', [
    '$scope'
    'Model'
    '$rootScope'

    ($scope, Model, $rootScope) ->
      $scope.getDataSetsDownloads = (modelId) ->
        model = $scope.model or new Model({id: modelId})
        model.$getDataSetDownloads()
        .then (opts) ->
          $scope.queuedIds = _.map opts.data.downloads, (download) ->
            parseInt download.dataset.id
          $scope.downloads = opts.data.downloads
        , (opts) ->
          $scope.setError(opts, 'loading dataset downloads request')

      $scope.requestDataSetDownload = (datasetId, modelId)->
        model = $scope.model or new Model({id: modelId})
        if datasetId in $scope.queuedIds
          $scope.setError {},
            "dataset #{datasetId} was already requested for download"
        else
          model.$putDataSetDownload(datasetId)
          .then (opts)->
            $scope.queuedIds.push datasetId
            $rootScope.msg = "DataSet has been queued for
            transformation/vectorization. Check Model > About for when
            it is ready for download"
          , (opts) ->
            $scope.setError opts,
              "requesting dataset #{datasetId} for download"
])