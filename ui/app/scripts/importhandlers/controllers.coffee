'use strict'

### Import Handlers specific Controllers ###

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
  '$dialog'
  'ImportHandler'

  ($scope, $rootScope, $routeParams, $dialog, ImportHandler) ->
    if not $routeParams.id
      err = "Can't initialize without import handler id"

    $scope.handler = new ImportHandler({_id: $routeParams.id})
    $scope.LOADED_SECTIONS = []
    $scope.PROCESS_STRATEGIES = ImportHandler.PROCESS_STRATEGIES

    $scope.go = (section) ->
      name = section[0]
      if name not in $scope.LOADED_SECTIONS
        $scope.handler.$load(
          show: ImportHandler.MAIN_FIELDS + ',queries,datasource'
        ).then (->
          $scope.LOADED_SECTIONS.push name
          $scope.handler.data = $scope.handler.getJsonData()
        ), ((opts) ->
          $scope.setError(opts, 'loading handler details')
        )
        if name == 'dataset'
          setTimeout(() ->
            $scope.$broadcast('loadDataSet', true)
            $scope.LOADED_SECTIONS.push name
          , 100)

    $scope.prepareDownload = () ->
      console.log "prep"

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

    $scope.saveData = () ->
      $scope.handler.$save(only: ['data'])
      .then (->), ((opts) ->
        $scope.setError(opts, 'saving handler details')
      )

    $scope.editDataSource = (handler, ds) ->
      $scope.openDialog($dialog, null,
        'partials/import_handler/datasource/edit_handler_datasource.html',
          'DataSourceEditDialogCtrl',
        'modal', 'edit data source', 'data source',
        {handler: handler, ds: ds}
      )

    $scope.initSections($scope.go)
    #$scope.initLogMessages("channel=importdata_log&model=" +
    #$scope.handler._id)
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
        handler: $scope.model._id,
        show: 'name,_id'
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
  '$dialog'
($scope, $dialog) ->
  $scope.importData = (handler) ->
    $scope.openDialog($dialog, handler,
    'partials/import_handler/load_data.html', 'LoadDataDialogCtrl')

  $scope.delete = (handler) ->
    $scope.openDialog($dialog, handler,
    'partials/base/delete_dialog.html', 'DeleteImportHandlerCtrl',
    "modal", "delete import handler", "/importhandlers")

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

.controller('AddImportHandlerQueryCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'ImportHandler'
  'Query'

($scope, $routeParams, $location, ImportHandler, Query) ->
  if not $routeParams.id then throw new Error "Specify id"

  $scope.handler = new ImportHandler({_id: $routeParams.id})
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
  $scope.PROCESS_STRATEGIES = ImportHandler.PROCESS_STRATEGIES

  $scope.handler = new ImportHandler({_id: $routeParams.id})
  $scope.model = new Item(
    {handler: $scope.handler, query_num: $routeParams.num, num: -1})

  $scope.$on('SaveObjectCtl:save:success', (event, current) ->
    $location.path($scope.handler.objectUrl())
  )
])
