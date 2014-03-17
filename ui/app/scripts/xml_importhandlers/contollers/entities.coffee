'use strict'

angular.module(
  'app.xml_importhandlers.controllers.entities', ['app.config', ])

# Entities and Fields Controllers

.controller('EntitiesTreeCtrl', [
  '$scope'
  '$rootScope'
  '$dialog'
  'Entity'
  'Field'

  ($scope, $rootScope, $dialog, Entity, Field) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.dialog = $dialog
      $rootScope.$on('BaseListCtrl:start:load', (event, name) ->
        if name == 'entities' then $scope.load()
      )
      $rootScope.$on('modelDeleted', () -> $scope.load())
      $scope.$watch('handler.entity', (entity, old, scope) ->
        if entity?
          $scope.objects = entity
      )

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
      $scope.openDialog({
        $dialog: $dialog
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
      $scope.openDialog({
        $dialog: $dialog
        model: field
        template: 'partials/xml_import_handlers/fields/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        list_model_name: "entities"
      })

    $scope.delete = (item) ->
      $scope.openDialog({
        $dialog: $dialog
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
      $scope.openDialog({
        $dialog: $dialog
        model: entity
        template: 'partials/xml_import_handlers/entities/edit_datasource.html'
        ctrlName: 'ModelEditDialogCtrl'
        list_model_name: "entities"
      })
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
