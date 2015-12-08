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
      script = new Script({
        import_handler_id: $scope.handler.id,
        type: 'python_code'
      })
      $scope.openDialog($scope, {
        model: script
        template: 'partials/importhandlers/xml/scripts/form.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add script'
      })

    $scope.edit = (script)->
      script.data_url = ''
      if script.type == 'python_file'
        script.data_url = script.data
      $scope.openDialog($scope, {
        model: script
        template: 'partials/importhandlers/xml/scripts/form.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'edit script'
      })

    $scope.preview = (script)->
      $scope.openDialog($scope, {
        model: script
        template: 'partials/importhandlers/xml/scripts/preview.html'
        ctrlName: 'ScriptPreviewCtrl'
        action: 'preview script'
      })

    $scope.delete = (script)->
      script.name = if script.type == 'python_file' then script.data else script.data.substr(0, 15) + '...'
      $scope.openDialog($scope, {
        model: script
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete script'
      })
])

.controller('ScriptPreviewCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    if openOptions.model?
      $scope.model = openOptions.model
    else
      throw new Error "Please specify a script"

    if $scope.model.type == 'python_file'
      $scope.name = $scope.model.data

    $scope.resetError()

    $scope.model.$getScriptString()
    .then (resp)->
      $scope.code = resp.data.script_string
    , (opts)->
      $scope.setError(opts, 'loading script')
])
