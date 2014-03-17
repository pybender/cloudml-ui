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
        extra: {'handler': $scope.handler}
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

    $scope.delete = (item)->
      $scope.openDialog({
        $dialog: $dialog
        model: item
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        list_model_name: "entities"
        action: 'delete'
      })
])