'use strict'

### Trained Model specific Controllers ###

angular.module('app.models.controllers', ['app.config', ])

.constant('MODEL_FIELDS',
  [ 'name','status','test_import_handler', 'train_import_handler',
    'train_import_handler_type', 'test_import_handler_type',
    'test_handler_fields', 'labels', 'classifier', 'error',
    'locked', 'training_in_progress','servers'].join(',')
)

.factory('FIELDS_BY_SECTION', [
  'MODEL_FIELDS'

  (MODEL_FIELDS) ->
    model: ['features_set_id','segments'].join(',')
    training: [
      'error','weights_synchronized','memory_usage','segments', 'trained_by',
      'trained_on','training_time','datasets', 'train_records_count',
      'trainer_size'
    ].join(',')
    about: [
      'created_on','target_variable','example_id','example_label',
      'updated_on','feature_count','created_by','data_fields',
      'test_handler_fields','tags','model_parts_size'
    ].join(',')
    main: MODEL_FIELDS
    grid_search: 'classifier_grid_params'
    visualization: [
      'visualization_data', 'segments'
    ]
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

  ($scope, $location, Model) ->
    $scope.MODEL = Model
    $scope.FIELDS = ['name','status','locked','servers',
                     'tags','created_on','created_by', 'updated_on',
                     'updated_by','comparable'].join(',')
    $scope.ACTION = 'loading models'
    $scope.currentTag = $location.search()['tag']
    $scope.STATUSES = ['', 'New', 'Queued', 'Importing',
    'Imported', 'Requesting Instance', 'Instance Started',
    'Training', 'Trained', 'Error', 'Canceled']

    $scope.init = (updatedByMe, modelName, sort_by, order) ->
      $scope.modelName = modelName
      $scope.kwargs = {
        tag: $scope.currentTag
        per_page: 5
        sort_by: sort_by
        order: order
        page: 1
      }
      $scope.$watch('user', (user, oldVal, scope) ->
        if user?
          if updatedByMe
            $scope.filter_opts = {
              'updated_by_id': user.id
              'status': ''}
            $scope.kwargs['page'] = 1
            $scope.$emit 'BaseListCtrl:start:load', modelName
          else
            $scope.filter_opts = {'status': ''}
      , true)

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

    # note: used to saving the file after choosing it.
    # othervise would be setted after changing another field.
    $scope.loadFile = ($fileContent) ->
      $scope.model.import_handler_file = $fileContent
      $scope.$apply()
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
  '$timeout'

  ($scope, $location, $routeParams, Model, Test, Tag, FIELDS_BY_SECTION, $q, $timeout) ->
    if not $routeParams.id
      throw new Error "Can't initialize without model id"

    $scope.model = new Model({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.params = {'tags': []}

    $scope.load = (fields, section) ->
      deferred = $q.defer()

      if not fields
        deferred.resolve 'empty fields'
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
          if section isnt 'modeljson'
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

      if name is 'model' && subsection is 'json'
        name = name + subsection
        subsection = ''

      if name in $scope.LOADED_SECTIONS
        return

      loadedSections = []
      if name is 'modeljson'
        $scope.load('features', 'modeljson').then ->
          # need to reload model.features each time because features may change
          # and JSON should be relevant, so dont push modeljson into loaded sections
        name = 'model'
        subsection = 'json'

      fields = ''
      if 'main' not in $scope.LOADED_SECTIONS
        loadedSections.push 'main'
        fields = FIELDS_BY_SECTION['main']

      if name is 'test'
        # A broad case is not going to work if we are landing directly, on
        # tests tab, we need to wait a bit for the tests tab to render before
        # broadcast an event
        $timeout ->
          $scope.$broadcast('loadTest', true)
        , 1

      if name not in $scope.LOADED_SECTIONS
        loadedSections.push name
        if FIELDS_BY_SECTION[name]?
          fields += ',' + FIELDS_BY_SECTION[name]

      $scope.load(fields, name).then ->
        for name in loadedSections
          if name not in $scope.LOADED_SECTIONS
            $scope.LOADED_SECTIONS.push name

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
      multiple: true
      query: (query) ->
        query.callback
          results: angular.copy($scope.tag_list)

      createSearchChoice: (term, data) ->
        cmp = () ->
          return this.text.localeCompare(term) == 0
        if $(data).filter(cmp).length == 0 then return {id: term, text: term}
    }

    # MATCH-1999: To fix angular-ui-select2 messing the ids and objects
    $scope.$watch 'params.tags', (newVal, oldVal)->
      if angular.isString(newVal) and newVal isnt ''
        ids = newVal.split(',')
        $scope.params.tags = []
        for id in ids
          nId = _.parseInt(id)
          if nId
            $scope.params.tags.push (t for t in $scope.tag_list when t.id is nId)[0]
          else
            $scope.params.tags.push {id: id, text: id}

    $scope.train_timer = null
    $scope.same_status_count = 0
    $scope.status = $scope.model.status
    $scope.monitorTraining = () ->
      $scope.train_timer = $timeout( ()->
          $scope.model.$load(
            show: 'status,training_in_progress,error,segments'
          ).then (->
            if $scope.model.status == $scope.status
              $scope.same_status_count += 1
            else
              $scope.status = $scope.model.status
              $scope.same_status_count = 0
            if $scope.model.training_in_progress && $scope.same_status_count < 20
              $scope.monitorTraining()
          )
        10000
      )

    $scope.$watch 'model.training_in_progress', (newVal, oldVal)->
      if newVal == true
        $scope.monitorTraining()

    $scope.$on '$destroy', (event) ->
      $timeout.cancel($scope.train_timer)

    $scope.updateTags = () ->
      $scope.model.tags = []
      for t in $scope.params['tags']
        $scope.model.tags.push t['text']

      $scope.model.$save(only: ['tags'])
      .then (->), (opts)->
        $scope.setError opts, 'saving model tags'

    $scope.$watch 'model.classifier.name', (nVal, oVal)->
      if nVal != oVal && $scope.model.classifier.predefined_selected
        $scope.model.$load(
          show: 'classifier'
        ).then (->
          $scope.model.classifier.name = nVal
        )

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
      openOptions.model.$train($scope.data).then ((resp) ->
        $scope.model.status = resp.data[$scope.model.API_FIELDNAME].status
        $scope.model.training_in_progress = true
        $scope.$close(true)
      ), ((opts) ->
        $scope.setError(opts, 'starting '+$scope.model.name+' training')
      )
])


.controller('GridSearchParametersCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'

  ($scope, $rootScope, openOptions) ->
    $scope.resetError()
    $scope.model = openOptions.model
    $scope.data = {
      parameters: {}
    }

    $scope.handler = $scope.model.train_import_handler_obj
    $scope.multiple_dataset = false

    classifier = $scope.model.classifier
    if !classifier.type?
      $scope.err = 'Need to specify classifier before performing grid search'
      $scope.inactive = true  # will hide parameters form
      return

    classifier.$getConfiguration(
    ).then ((opts) ->
      $scope.params = opts.data.configuration[classifier.type]["parameters"]
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

    $scope.start = (result) ->
      openOptions.model.$classifierGridSearch($scope.data).then (() ->
        $scope.model.grid_search_in_progress = true
        $scope.$close(true)
        $rootScope.setSection ['grid_search', 'details']
      ), ((opts) ->
        $scope.setError(opts, 'starting '+$scope.model.name+' searching for classifier parameters')
      )
])


.controller('GridSearchResultsCtrl', [
  '$scope'

  ($scope) ->
    $scope.open_logs_calc_id = null
    $scope.reload_counter = 0

    $scope.showLogs = (id) ->
      if $scope.open_logs_calc_id == id
        $scope.open_logs_calc_id = null
      else
        $scope.open_logs_calc_id = id

    $scope.$watch 'model.grid_search_in_progress', (newVal, oldVal)->
      if newVal == true
        $scope.reload()

    $scope.reload = () ->
      $scope.model.$load({show: 'classifier_grid_params'}).then((resp) ->
        statuses = []
        statuses.push c.status for c in $scope.model.classifier_grid_params
        if ('New' in statuses || 'Queued' in statuses || 'Calculating' in statuses) &&
            $scope.reload_counter < 20
          $scope.model.grid_search_in_progress = true
          $scope.reload_counter += 1
          window.setTimeout(
            () -> $scope.reload()
            5000)
        else
          $scope.model.grid_search_in_progress = false
      )
])

.controller('CloneModelCtrl', [
  '$scope'
  '$rootScope'
  'openOptions'
  '$location'
  'Model'

  ($scope, $rootScope, openOptions, $location, Model) ->
    $scope.resetError()
    $scope.model = openOptions.model

    $scope.clone = (result) ->
      openOptions.model.$clone().then ((opts) ->
        model = new Model(opts.data.model)
        $scope.$close(true)
        $location.url(model.objectUrl())
      ), ((opts) ->
        $scope.setError(opts, 'error cloning the '+$scope.model.name)

      )
])

.controller('ModelActionsCtrl', [
  '$scope'
  '$route'

  ($scope, $route) ->
    $scope.init = (opts) ->
      if not opts or not opts.model
        throw new Error "Please specify model"

      $scope.model = opts.model

    $scope.test_model = (model)->
      $scope._showModelActionDialog(model, 'test', (model) ->
        model.$load(show: 'test_handler_fields').then (->
          $scope.openDialog($scope, {
            model: model
            template: 'partials/testresults/run_test.html'
            ctrlName: 'TestDialogController'
            cssClass: 'modal large'
          }))
        )

    $scope.cancel_request_spot_instance = (model)->
      model.$cancel_request_spot_instance()

    $scope.grid_search_params = (model)->
      $scope._showModelActionDialog(model, 'train', (model) ->
        $scope.openDialog($scope, {
          model: model
          template: 'partials/models/grid_search.html'
          ctrlName: 'GridSearchParametersCtrl'
        }))

    $scope.train_model = (model)->
      $scope._showModelActionDialog(model, 'train', (model) ->
        $scope.openDialog($scope, {
          model: model
          template: 'partials/models/model_train_popup.html'
          ctrlName: 'TrainModelCtrl'
        }))

    $scope.delete_model = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete model'
        path: model.BASE_UI_URL
      })

    $scope.cloneModel = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/models/clone_model_popup.html'
        ctrlName: 'CloneModelCtrl'
        action: 'clone model'
        path: model.BASE_UI_URL
      })


    $scope.editClassifier = (model) ->
      $scope.backupClassifier = angular.copy(model.classifier)
      $scope.openDialog($scope, {
        model: null
        template: 'partials/features/classifiers/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit classifier'
        extra: {model: model, fieldname: 'classifier'}
      })
      .result
      .then ->
        $scope.backupClassifier = null
      , ->
        model.classifier = $scope.backupClassifier
        $scope.backupClassifier = null

    $scope.uploadModelToPredict = (model) ->
      $scope.openDialog($scope, {
        model: model
        template: 'partials/servers/choose_server_for_model.html'
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

    $scope.import_ih_fields_to_features = ->
      $scope.model.$add_ih_fields_as_features()
      .then ->
        $route.reload()
      , (opts) ->
        $scope.setError(opts, 'adding training import handler fields as features')
  ])

.controller('ModelFeaturesJsonEditCtrl', [
    '$scope'
    '$route'
    ($scope, $route)->
      $scope.$watch 'model.features', (newValue)->
        if not newValue or $scope.model.originalJson
          return
        $scope.model.originalJson = newValue
      $scope.resetJsonChanges = ->
        $scope.model.features = $scope.model.originalJson
        $scope.FeaturesJsonForm.fJson.$setPristine()
      $scope.saveJson = ->
        $scope.model.$save(only: ['features'])
        .then () ->
          $route.reload()
        , (opts)->
          $scope.setError(opts, 'saving model features JSON')
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
    '$timeout'

    ($scope, Model, $rootScope, $timeout) ->
      $scope.downloadRequested = false
      $rootScope.dl_msg = ""
      $rootScope.downloads = {}

      $scope.getDataSetsDownloads = (modelId) ->
        model = $scope.model or new Model({id: modelId})
        model.$getDataSetDownloads()
        .then (opts) ->
          $rootScope.downloads = opts.data.downloads
        , (opts) ->
          $scope.setError(opts, 'loading dataset downloads request')

      $scope.requestDataSetDownload = (datasetId, modelId)->
        model = $scope.model or new Model({id: modelId})
        $scope.downloadRequested = true
        $rootScope.dl_msg = "Checking in-progress requests for DataSet transformation/vectorization ... "
        $timeout ->
          model.$getDataSetDownloads()
          .then (opts) ->
            $rootScope.downloads = opts.data.downloads
            statuses = []
            for d in $scope.downloads
              statuses.push d.task.status
            if 'In Progress' in statuses
              $rootScope.dl_msg = "Please, check in-progress DataSet transformation request on
              Model > About tab. Try to reload page to see it and it's status updates."
            else
              model.$putDataSetDownload datasetId
              .then (opts)->
                $rootScope.dl_msg = "DataSet has been queued for
                transformation/vectorization. Check its status on Model > About tab
                when it is ready for download. (Reload page to see status updates)"
                $timeout ->
                  $scope.getDataSetsDownloads modelId
                , 5000
              , (opts) ->
                $scope.downloadRequested = false
                $scope.setError opts,
                  "requesting dataset #{datasetId} for download"
          , (opts) ->
            $scope.downloadRequested = false
            $scope.setError(opts, 'loading dataset downloads request')
        , 5000
])

.controller('ModelVisualizationCtrl', [
    '$scope'

    ($scope) ->
      $scope.mode = 'visual'
      $scope.$watch('action', (val, oldVal) ->
        if val?
          $scope.mode = val[1]
      , true)
])


.controller('TreeDeepFormCtrl', [
    '$scope'
    'Model'
    '$timeout'

    ($scope, Model, $timeout) ->
      $scope.msg = ''
      $scope.showTreeDeepForm = false

      $scope.init = (model, segment) ->
        $scope.model = model
        $scope.segment = segment
        $scope.$watch('model.visualization_data[segment.name].parameters.deep', (val, oldVal) ->
          if val?
            $scope.treeDeep = val
        , true)

      $scope.generate = (model) ->
        $scope.msg = 'Please wait! Visualization tree is re-generating now... Tree will be updated when re-generation would be completed.'
        $scope.model.$regenerateVisualization({
          parameters: {deep: $scope.treeDeep}
          type: 'tree_deep'
        }).then (() ->
          $scope.timer = $timeout($scope.checkVisualization, 2000)
          $scope.showTreeDeepForm = false
        ), ((opts) ->
          $scope.setError(opts, 'queue regenerating visualization tree task')
        )

      $scope.checkVisualization = () ->
        $scope.model.$load(show: 'visualization_data')
        .then (opts) ->
          if $scope.model.visualization_data[$scope.segment.name].parameters.status == 'done'
            $scope.timer = null
            $scope.msg = ''
          else
            $scope.timer = $timeout($scope.checkVisualization, 2000)
        , (opts) ->
          $scope.setError(opts, 'loading model visualization details')

])


.controller('FeaturesTransformersDataCtrl', [
    '$scope'
    'Model'
    '$rootScope'
    '$timeout'

    ($scope, Model, $rootScope, $timeout) ->
      $scope.downloadRequested = false
      $rootScope.tf_dl_msg = ""
      $rootScope.tf_downloads = {}
      $scope.tf_segment = ''
      $scope.tf_format = ''
      $scope.formats = [{name: 'JSON', value: 'json'},
                        {name: 'CSV', value: 'csv'}]
      $scope.open_logs_task_id = null

      $scope.getTransformersDownloads = (modelId) ->
        model = $scope.model or new Model({id: modelId})
        model.$getTransformersDataDownloads()
        .then (opts) ->
          $rootScope.tf_downloads = opts.data.downloads
          $rootScope.tf_dl_msg = ''
          statuses = []
          statuses.push c.task.status for c in ($rootScope.tf_downloads)
          console.log statuses
          if 'In Progress' in statuses
            $timeout ->
              $scope.getTransformersDownloads modelId
            , 5000
        , (opts) ->
          $scope.setError(opts, 'loading transformers downloads')

      $scope.requestTransformersDownload = (modelId)->
        model = $scope.model or new Model({id: modelId})
        model.$putTransformersDataDownload $scope.tf_segment, $scope.tf_format
        .then (opts)->
          $rootScope.tf_dl_msg = "Segment data has been queued for
          download. Reload page to check status updates if downloads don't
          appear in 5 seconds"
          $timeout ->
            $scope.getTransformersDownloads modelId
          , 5000
        , (opts) ->
          $scope.setError(opts, 'requesting transformers downloads')

      $scope.showLogs = (id) ->
        if $scope.open_logs_task_id == id
          $scope.open_logs_task_id = null
        else
          $scope.open_logs_task_id = id

])
