'use strict'

angular.module(
  'app.importhandlers.xml.controllers.scripts', ['app.config', ])

.controller('ScriptsListCtrl', [
  '$scope'
  'Script'

  ($scope, Script) ->
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
      $scope.resetError()
      script = new Script({
        import_handler_id: $scope.handler.id
      })
      $scope.openDialog($scope, {
        model: script
        template: 'partials/importhandlers/xml/scripts/add.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add script'
      })

    $scope.edit = (script)->
      $scope.resetError()
      $scope.openDialog($scope, {
        model: script
        template: 'partials/importhandlers/xml/scripts/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'edit script'
      })

    $scope.delete = (script)->
      $scope.resetError()
      $scope.openDialog($scope, {
        model: script
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete script'
      })
])
