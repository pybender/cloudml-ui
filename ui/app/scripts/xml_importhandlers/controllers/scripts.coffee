'use strict'

angular.module(
  'app.xml_importhandlers.controllers.scripts', ['app.config', ])

.controller('ScriptsListCtrl', [
  '$scope'
  '$modal'
  'Script'

  ($scope, $modal, Script) ->
    $scope.MODEL = Script
    $scope.FIELDS = Script.MAIN_FIELDS
    $scope.ACTION = 'loading scripts'

    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.xml_scripts', (scripts, old, scope) ->
        if scripts?
          $scope.objects = scripts
      )

    $scope.add = () ->
      script = new Script({
        import_handler_id: $scope.handler.id,
        data: ''
      })
      $scope.openDialog({
        $modal: $modal
        model: script
        template: 'partials/xml_import_handlers/scripts/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add script'
      })

    $scope.edit = (script)->
      script = new Script(script)
      $scope.openDialog({
        $modal: $modal
        model: script
        template: 'partials/xml_import_handlers/scripts/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'edit script'
      })

    $scope.delete = (script)->
      script = new Script(script)
      $scope.openDialog({
        $modal: $modal
        model: script
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete script'
      })
])
