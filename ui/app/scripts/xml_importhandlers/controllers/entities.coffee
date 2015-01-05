'use strict'

angular.module(
  'app.xml_importhandlers.controllers.entities', ['app.config', ])

# Entities and Fields Controllers

.controller('EntitiesTreeCtrl', [
  '$scope'
  '$rootScope'
  'Entity'
  'Field'
  'Sqoop'
  'XmlImportHandler'

  ($scope, $rootScope, Entity, Field, Sqoop, XmlImportHandler) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $rootScope.$on('BaseListCtrl:start:load', (event, name) ->
        if name == 'entities' then $scope.load()
      )
      $scope.$watch('handler.entity', (entity, old, scope) ->
        if entity?
          $scope.objects = entity
      )
      $scope.query_msg = {}

    $scope.load = () ->
      $scope.handler.$load({'show': 'entities'}).then (
        (opts) ->), ((opts) ->
        $scope.setError(opts, "loading entities tree")
      )

    $scope.addEntity = (entity) ->
      ent = new Entity({
        'import_handler_id': entity.import_handler_id
        'entity_id': entity.id
      })
      $scope.openDialog($scope, {
        model: ent
        template: 'partials/xml_import_handlers/entities/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        list_model_name: "entities"
      })

    $scope.addField = (entity) ->
      field = new Field({
        'import_handler_id': entity.import_handler_id
        'entity_id': entity.id
      })
      $scope.openDialog($scope, {
        model: field
        template: 'partials/xml_import_handlers/fields/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        list_model_name: "entities"
      })

    $scope.delete = (item) ->
      $scope.openDialog($scope, {
        model: item
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        list_model_name: "entities"
        action: 'delete'
      })

    $scope.editDataSource = (entity) ->
      entity = new Entity({
        id: entity.id
        name: entity.name
        import_handler_id: entity.import_handler_id
        datasource: entity.datasource_id
        transformed_field: entity.transformed_field_id
        entity_id: entity.entity_id
      })
      $scope.openDialog($scope, {
        model: entity
        template: 'partials/xml_import_handlers/entities/edit_datasource.html'
        ctrlName: 'ModelEditDialogCtrl'
        list_model_name: "entities"
      })

    $scope.saveQueryText = (query) ->
      if not query.text
        query.edit_err = 'Please enter the query text'
        return
      query.loading_state = true
      query.$save({only: ['text']}).then((opts) ->
        query.loading_state = false
        query.msg = 'Query has been saved'
        query.edit_err = null
        query.err = null
      )

    $scope.runQuery = (queryObj) ->
      $scope.openDialog($scope, {
        model: null
        template: 'partials/import_handler/test_query.html'
        ctrlName: 'QueryTestDialogCtrl'
        extra:
          handlerUrl: "#{$scope.handler.BASE_API_URL}#{$scope.handler.id}"
          datasources: $scope.handler.xml_data_sources
          query: queryObj
        action: 'test xml import handler query'
      })

    $scope.addSqoop = (entity) ->
      sqoop = new Sqoop({
        'import_handler_id': entity.import_handler_id
        'entity_id': entity.id
        'entity': entity.id
      })
      $scope.openDialog($scope, {
        model: sqoop
        template: 'partials/xml_import_handlers/sqoop/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        list_model_name: "entities"
      })

    $scope.getPigFields = (sqoop) ->
      $scope.openDialog($scope, {
        model: sqoop
        template: 'partials/xml_import_handlers/sqoop/load_pig_fields.html'
        ctrlName: 'PigFieldsLoader'
      })

])

.controller('PigFieldsLoader', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.sqoop = openOptions.model
    $scope.err = ""
    $scope.sqoop.getPigFields().then((resp) ->
      $scope.fields = resp.data.fields
      $scope.generated_pig_string = resp.data.sample
      $scope.pig_result_line = resp.data.pig_result_line
    , ((opts) ->
      $scope.err = opts.data.response.error.message
      $scope.setError(opts, 'loading pig fields')
    ))
])

.controller('XmlTransformedFieldSelectCtrl', [
  '$scope'
  'Field'

  ($scope, Field) ->
    $scope.init = (entity) ->
      $scope.entity = entity
      if $scope.entity.entity_id
        $scope.load()
      else
        $scope.transformed_fields = []

    $scope.load = () ->
      Field.$loadAll(
        show: 'name'
        import_handler_id: $scope.entity.import_handler_id
        entity_id: $scope.entity.entity_id
        transformed: true
      ).then ((opts) ->
        $scope.transformed_fields = opts.objects
      ), ((opts) ->
        $scope.setError(opts, 'loading transformed fields')
      )
])
