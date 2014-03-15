'use strict'

angular.module(
  'app.xml_importhandlers.controllers.entities', ['app.config', ])

# Entities and Fields Controllers

.controller('EntitiesTreeCtrl', [
  '$scope'
  '$rootScope'
  '$dialog'
  'Entity'

  ($scope, $rootScope, $dialog, Entity) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $rootScope.$on('BaseListCtrl:start:load', (event, name) ->
        if name == 'entities' then $scope.load()
      )
      $rootScope.$on('modelDeleted', () -> $scope.load())
      $scope.$watch('handler.entity', (entity, old, scope) ->
        if entity?
          $scope.objects = entity
      )

    $scope.load = () ->
      $scope.handler.$load({'show': 'entities,xml'}).then (
        (opts) ->), ((opts) ->
        $scope.setError(opts, "loading entities tree")
      )

    $scope.addEntity = (entity) ->
      ent = new Entity({
        'import_handler_id': entity.import_handler_id
        'entity_id': entity.id
      })
      $scope.openDialog($dialog, ent,
        'partials/xml_import_handlers/entities/edit.html',
        'ModelEditDialogCtrl', 'modal', 'add entity',
        list_model_name="entities")

    $scope.addField = (entity) ->
      field = new Field({
        'import_handler_id': entity.import_handler_id
        'entity_id': entity.id
      })
      $scope.openDialog($dialog, field,
        'partials/xml_import_handlers/fields/edit.html',
        'ModelEditDialogCtrl', 'modal', 'add field',
        list_model_name="entities")

    $scope.delete = (item)->
      $scope.openDialog($dialog, item,
        'partials/base/delete_dialog.html', 'DialogCtrl',
        'modal', 'delete', list_model_name="entities")
])