describe 'xml_importhandlers/controllers/scripts.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.xml_importhandlers.controllers.scripts'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $scope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'ScriptsListCtrl', ->

    it 'should init scope and watch handler.xml_scripts and call onto openDialog',
      inject (Script, XmlImportHandler)->
        handler = new XmlImportHandler
          id: 111
          name: 'xml_ih'
        createController 'ScriptsListCtrl', {Script: Script}

        expect($scope.MODEL).toEqual Script
        expect($scope.FIELDS).toEqual Script.MAIN_FIELDS
        expect($scope.ACTION).toEqual 'loading scripts'

        # init & watch
        $scope.init handler
        expect($scope.handler).toEqual handler
        expect($scope.kwargs).toEqual {'import_handler_id': handler.id}
        $scope.$digest() # to trigger the watch
        expect($scope.objects).toBeUndefined()

        # watch
        scripts = [
          id: 222
          data: 'script 222 data'
        ,
          id: 333,
          data: 'script 333 data'
        ]
        handler.xml_scripts = scripts
        $scope.$digest() # to trigger the watch
        expect($scope.objects).toEqual handler.xml_scripts

        handler.xml_scripts.pop()
        $scope.$digest() # to trigger the watch
        expect($scope.objects).toEqual handler.xml_scripts

        $scope.openDialog = jasmine.createSpy 'openDialog'

        # add dialog
        $scope.add()
        expect($scope.openDialog).toHaveBeenCalled()
        openOptions = $scope.openDialog.calls.mostRecent().args[0]
        expect(openOptions.model.import_handler_id).toEqual 111
        expect(openOptions.model.data).toEqual ''
        expect(openOptions.template).toEqual 'partials/xml_import_handlers/scripts/edit.html'
        expect(openOptions.ctrlName).toEqual 'ModelEditDialogCtrl'
        expect(openOptions.action).toEqual 'add script'

        # edit dialog
        script = new Script {id: 999, import_handler_id: 888, data: 'to edit'}
        $scope.edit(script)
        expect($scope.openDialog).toHaveBeenCalled()
        openOptions = $scope.openDialog.calls.mostRecent().args[0]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.template).toEqual 'partials/xml_import_handlers/scripts/edit.html'
        expect(openOptions.ctrlName).toEqual 'ModelEditDialogCtrl'
        expect(openOptions.action).toEqual 'edit script'

        # delete dialog
        script = new Script {id: 888, import_handler_id: 777, data: 'to delete'}
        $scope.delete(script)
        expect($scope.openDialog).toHaveBeenCalled()
        openOptions = $scope.openDialog.calls.mostRecent().args[0]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.template).toEqual 'partials/base/delete_dialog.html'
        expect(openOptions.ctrlName).toEqual 'DialogCtrl'
        expect(openOptions.action).toEqual 'delete script'
