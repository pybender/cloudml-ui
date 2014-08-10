'use strict'

### Import Handlers specific Controllers ###
EXTRA_TARGET_FEATURES_PARAMS = {
  'json': ['jsonpath', 'to_csv', 'key_path', 'value_path'],
  'composite': ['expression']}

READABILITY_TYPES = [
  'ari', 'flesch_reading_ease', 'flesch_kincaid_grade_level',
  'gunning_fog_index', 'smog_index', 'coleman_liau_index', 'lix', 'rix']

angular.module('app.importhandlers.controllers', ['app.config', ])

.controller('ImportHandlerListCtrl', [
  '$scope'
  '$rootScope'
  'ImportHandler'

($scope, $rootScope, ImportHandler) ->
  $scope.MODEL = ImportHandler
  $scope.FIELDS = ImportHandler.MAIN_FIELDS
  $scope.ACTION = 'loading handler list'
])

.controller('ImportHandlerDetailsCtrl', [
  '$scope'
  '$rootScope'
  '$routeParams'
  '$modal'
  'ImportHandler'

  ($scope, $rootScope, $routeParams, $modal, ImportHandler) ->
    if not $routeParams.id
      err = "Can't initialize without import handler id"

    $scope.handler = new ImportHandler({id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.PROCESS_STRATEGIES =
      _.sortBy ImportHandler.PROCESS_STRATEGIES, (s)-> s

    $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        fields = ImportHandler.MAIN_FIELDS + ',data'
        if mainSection == 'dataset'
          setTimeout(() ->
            $scope.$broadcast('loadDataSet', true)
            $scope.LOADED_SECTIONS.push mainSection
          , 100)

      if fields != ''
        $scope.handler.$load(
            show: fields
        ).then (->
          $scope.LOADED_SECTIONS.push mainSection
        ), ((opts) ->
          $scope.setError(opts, 'loading handler details')
        )

    $scope.save = (fields) ->
      $scope.handler.$save(only: fields)
      .then (->), ((opts) ->
        $scope.setError(opts, 'saving import handler')
      )

    $scope.makeRequired = (item, is_required) ->
      item.is_required = is_required
      item.$save({only: ['is_required']})

    $scope.deleteQuery = (queries, query) ->
      index = queries.indexOf(query)
      query.$remove().then(()->
        # Reorganize indexes
        for i in [queries.length - 1..0] by -1
          q = queries[i]
          if q.num == index
            queries.splice(index, 1)
            break
          else
            q.num -= 1
      )

    $scope.deleteItem = (items, item) ->
      index = items.indexOf(item)
      item.$remove().then(()->
        # Reorganize indexes
        for i in [items.length - 1..0] by -1
          it = items[i]
          if it.num == index
            items.splice(index, 1)
            break
          else
            it.num -= 1
      )

    $scope.deleteFeature = (features, feature) ->
      index = features.indexOf(feature)
      feature.$remove().then(()->
        # Reorganize indexes
        for i in [features.length - 1..0] by -1
          it = features[i]
          if it.num == index
            features.splice(index, 1)
            break
          else
            it.num -= 1
      )

    $scope.saveData = () ->
      $scope.handler.$save(only: ['data'])
      .then (->), ((opts) ->
        $scope.setError(opts, 'saving handler details')
      )

    $scope.editDataSource = (handler, ds) ->
      $scope.openDialog({
        $modal: $modal
        model: null
        template: \
          'partials/import_handler/datasource/edit_handler_datasource.html'
        ctrlName: 'DataSourceEditDialogCtrl'
        action: 'add data source'
        extra: {handler: handler, ds: ds}
      })

    $scope.editTargetFeature = (item, feature) ->
      $scope.openDialog({
        $modal: $modal
        model: null
        template: 'partials/import_handler/edit_target_feature.html'
        ctrlName: 'TargetFeatureEditDialogCtrl'
        extra: {handler: item.handler, feature: feature, item: item}
        action: 'edit target feature'
      })

    $scope.runQuery = (query) ->
      $scope.openDialog({
        $modal: $modal
        model: null
        template: 'partials/import_handler/test_query.html'
        ctrlName: 'QueryTestDialogCtrl'
        extra:
          handlerUrl: $scope.handler.getUrl()
          datasources: $scope.handler.datasource,
          query: query
        action: 'test import handler query'
      })

    $scope.initSections($scope.go)
])

.controller('QueryTestDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.handlerUrl = dialog.extra.handlerUrl
    $scope.datasources = (ds for ds in dialog.extra.datasources when \
      ds.type is 'sql' or ds.type is 'db')
    $scope.query = dialog.extra.query
    $scope.params = $scope.query.getParams()
    $scope.dialog = dialog

    if !$scope.query.test_params
      $scope.query.test_params = {}
    if !$scope.query.test_limit
      $scope.query.test_limit = 2
    if !$scope.query.test_datasource
      $scope.query.test_datasource = $scope.datasources[0].name

    $scope.runQuery = () ->
      $scope.query.test = {}
      $scope.query.$run($scope.query.test_limit, $scope.query.test_params,
        $scope.query.test_datasource, $scope.handlerUrl
      ).then((resp) ->
        $scope.query.test.columns = resp.data.columns
        $scope.query.test.data = resp.data.data
        $scope.query.test.sql = resp.data.sql
        dialog.close()
      , ((opts) ->
        $scope.query.test.error = $scope.setError(opts, 'testing sql query')
      ))
])

.controller('ImportTestDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.handler = dialog.extra.handler
    $scope.params = $scope.handler.import_params
    $scope.parameters = {}
    $scope.test_limit = 2
    $scope.dialog = dialog
    $scope.err = ''

    $scope.runTestImport = () ->
      $scope.handler.$getTestImportUrl($scope.parameters, $scope.test_limit
      ).then((resp) ->
        dialog.close()
        window.location = resp.data.url
      , ((opts) ->
        $scope.err = $scope.setError(opts, 'testing import handler')
      ))
])

.controller('DataSourceEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.handler = dialog.extra.handler
    $scope.model = dialog.extra.ds
    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
      $scope.handler.$load(
        show: 'datasource'
      ).then (->), (-> $scope.setError(opts, 'loading datasource details'))
    )
])


.controller('TargetFeatureEditDialogCtrl', [
  '$scope'
  '$rootScope'
  'dialog'
  'TargetFeature'

  ($scope, $rootScope, dialog, TargetFeature) ->
    $scope.handler = dialog.extra.handler
    feature = dialog.extra.feature
    item = dialog.extra.item
    if !feature?
        feature = new TargetFeature({
          handler: $scope.handler,
          query_num: item.query_num,
          item_num: item.num,
          num: -1
          })
    $scope.model = feature
    $scope.item = item
    $scope.DONT_REDIRECT = true
    $scope.dialog = dialog

    $scope.fields = ['name']
    extra = EXTRA_TARGET_FEATURES_PARAMS[item.process_as]
    if extra?
      $scope.fields = $scope.fields.concat(extra)

    $scope.readabilityTypes = READABILITY_TYPES

    $scope.$on('SaveObjectCtl:save:success', (event, current) ->
      dialog.close()
      if $scope.model.isNew()
        $scope.model.num = $scope.item.target_features.length
        $scope.item.target_features.push $scope.model
    )
])

.controller('AddImportHandlerCtl', [
  '$scope'
  'ImportHandler'

  ($scope, ImportHandler) ->
    $scope.types = [{name: 'Db'}, {name: 'Request'}]
    $scope.model = new ImportHandler()
])

.controller('DeleteImportHandlerCtrl', [
  '$scope'
  '$location'
  'dialog'
  'Model'

  ($scope, $location, dialog, Model) ->
    $scope.resetError()
    $scope.MESSAGE = dialog.action
    $scope.model = dialog.model
    $scope.path = dialog.path
    $scope.action = dialog.action
    $scope.extra_template = '/partials/import_handler/extra_delete.html'

    $scope.loadModels = () ->
      Model.$by_handler(
        handler: $scope.model.id,
        show: 'name,id'
      ).then ((opts) ->
        $scope.umodels = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading models that use import handler')
      )

    $scope.loadModels()

    $scope.close = ->
      dialog.close()
])


.controller('ImportHandlerActionsCtrl', [
  '$scope'
  '$modal'
($scope, $modal) ->
  $scope.importData = (handler) ->
    $scope.openDialog({
      $modal: $modal
      model: handler
      template: 'partials/import_handler/load_data.html'
      ctrlName: 'LoadDataDialogCtrl'
    })

  $scope.delete = (handler) ->
    $scope.openDialog({
      $modal: $modal
      model: handler
      template: 'partials/base/delete_dialog.html'
      ctrlName: 'DeleteImportHandlerCtrl'
      action: 'delete import handler'
      path: "/handlers/#{handler.TYPE}"
    })

  $scope.testHandler = (handler) ->
    $scope.openDialog({
      $modal: $modal
      template: 'partials/import_handler/test_handler.html'
      ctrlName: 'ImportTestDialogCtrl'
      action: 'test import handler'
      extra: {handler: $scope.handler}
    })

  $scope.uploadHandlerToPredict = (model) ->
    $scope.openDialog({
      $modal: $modal
      model: model
      template: 'partials/servers/choose.html'
      ctrlName: 'ImportHandlerUploadToServerCtrl'
    })
])

.controller('ImportHandlerUploadToServerCtrl', [
  '$scope'
  '$rootScope'
  'dialog'

  ($scope, $rootScope, dialog) ->
    $scope.dialog = dialog
    $scope.resetError()
    $scope.model = dialog.model
    $scope.model.server = null

    $scope.upload = () ->
      $scope.model.$uploadPredict($scope.model.server).then((resp) ->
        $rootScope.msg = resp.data.status
      )
      dialog.close()
])


.controller('ImportHandlerSelectCtrl', [
  '$scope'
  'ImportHandler'
  'XmlImportHandler'

  ($scope, ImportHandler, XmlImportHandler) ->
    ImportHandler.$loadAll show: 'name'
    .then (opts) ->
      $scope.handlers = []
      $scope.handlers_list = []
      $scope.handlers = $scope.handlers.concat opts.objects
      for h in $scope.handlers
        $scope.handlers_list.push {value: h.id, text: h.name}
      XmlImportHandler.$loadAll show: 'name'
    .then (opts) ->
      $scope.handlers = $scope.handlers.concat opts.objects
      for h in opts.objects
        item = {value: h.id + "xml", text: h.name + "(xml)"}
        $scope.handlers_list.push item
      $scope.handlers_list = _.sortBy $scope.handlers_list, (o)-> o.text
    , (opts) ->
      $scope.setError(opts, 'loading import handler list')
])

.controller('AddImportHandlerQueryCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'ImportHandler'
  'Query'

($scope, $routeParams, $location, ImportHandler, Query) ->
  if not $routeParams.id then throw new Error "Specify id"

  $scope.handler = new ImportHandler({id: $routeParams.id})
  $scope.model = new Query(
    {handler: $scope.handler, num: -1})

  $scope.$on('SaveObjectCtl:save:success', (event, current) ->
    $location.path($scope.handler.objectUrl())
  )
])

.controller('AddImportHandlerQueryItemCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'ImportHandler'
  'Item'

($scope, $routeParams, $location, ImportHandler, Item) ->
  if not $routeParams.id then throw new Error "Specify id"
  if not $routeParams.num then throw new Error "Specify query number"
  $scope.PROCESS_STRATEGIES =
    _.sortBy ImportHandler.PROCESS_STRATEGIES, (s)-> s

  $scope.handler = new ImportHandler({id: $routeParams.id})
  $scope.model = new Item(
    {handler: $scope.handler, query_num: $routeParams.num, num: -1})

  $scope.$on('SaveObjectCtl:save:success', (event, current) ->
    $location.path($scope.handler.objectUrl())
  )
])
