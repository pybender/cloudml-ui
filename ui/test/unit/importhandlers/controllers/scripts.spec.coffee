describe 'importhandlers/xml/controllers/scripts.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.importhandlers.xml.controllers.scripts'

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
        expect($scope.objects).toEqual([])

        # watch
        scripts = [
          id: 222
          data: 'script 222 data'
          type: 'python_code'
        ,
          id: 333,
          data: 'script 333 data'
          type: 'python_code'
        ,
          id: 444,
          data: 'functions.py'
          type: 'python_file'

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
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Script
          template: 'partials/importhandlers/xml/scripts/form.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'add script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual 111

        # edit dialog
        script = new Script {id: 999, import_handler_id: 888, data: 'to edit'}
        $scope.edit(script)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Script
          template: 'partials/importhandlers/xml/scripts/form.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'edit script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data

        # edit dialog
        script = new Script {id: 999, import_handler_id: 888, data: 'some.url', type: 'python_file'}
        $scope.edit(script)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Script
          template: 'partials/importhandlers/xml/scripts/form.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'edit script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.model.data_url).toEqual script.data_url

        # delete dialog
        script = new Script {id: 888, import_handler_id: 777, data: 'some code some code ', type: 'python_code'}
        $scope.delete(script)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: script
          template: 'partials/base/delete_dialog.html'
          ctrlName: 'DialogCtrl'
          action: 'delete script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.model.name).toEqual 'some code some ...'

        script = new Script {id: 888, import_handler_id: 777, data: 'some/url.py', type: 'python_file'}
        $scope.delete(script)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: script
          template: 'partials/base/delete_dialog.html'
          ctrlName: 'DialogCtrl'
          action: 'delete script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.model.name).toEqual script.data

        # preview dialog
        script = new Script {id: 999, import_handler_id: 888, data: '333', type: 'python_code'}
        $scope.preview(script)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any Script
          template: 'partials/importhandlers/xml/scripts/preview.html'
          ctrlName: 'ScriptPreviewCtrl'
          action: 'preview script'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
        openOptions = $scope.openDialog.calls.mostRecent().args[1]
        expect(openOptions.model.import_handler_id).toEqual script.import_handler_id
        expect(openOptions.model.id).toEqual script.id
        expect(openOptions.model.data).toEqual script.data
        expect(openOptions.model.type).toEqual script.type


  describe 'ScriptPreviewCtrl', ->

    it 'should handle openOptions with model', ->
      openOptions =
        model:
          Script =
            id: 22
            import_handler_id: 55
            type: 'python_file'
            data: 'url/to/file.py'

      url = "#{settings.apiUrl}xml_import_handlers/#{openOptions.model.import_handler_id}/scripts/#{openOptions.model.id}/action/script_string/"

      it 'should get script string with python_file type', ->
        $httpBackend.expectGET(url).respond 200, angular.toJson
          script:
            id: 22
          script_string: '3+5'

        createController 'ScriptPreviewCtrl', {$scope: {}, openOptions: openOptions}
        expect($scope.model).toEqual openOptions.model
        httpBackend.flush()
        expect($scope.code).toEqual '3+5'
        expect($scope.name).toEqual openOptions.model.data

      it 'should get script string with python_code type', ->
        $httpBackend.expectGET(url).respond 200, angular.toJson
          script:
            id: 22
          script_string: '3+5'
        openOptions.model.type = 'python_code'
        openOptions.model.data = '3+5'
        createController 'ScriptPreviewCtrl', {$scope: {}, openOptions: openOptions}
        expect($scope.model).toEqual openOptions.model
        httpBackend.flush()
        expect($scope.code).toEqual '3+5'
        expect($scope.name).toBeUndefined

      it 'should set error on get script string', ->
        $httpBackend.expectGET(url).respond 400
        createController 'ScriptPreviewCtrl', {$scope: {}, openOptions: openOptions}
        expect($scope.model).toEqual openOptions.model
        httpBackend.flush()
        expect($scope.code).toBeUndefined
        expect($scope.name).toBeUndefined

    it 'should throw error', ->
      expect ->
        createController 'ScriptPreviewCtrl', {openOptions: {}}
      .toThrow new Error "Please specify a script"

