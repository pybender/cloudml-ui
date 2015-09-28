describe 'xml_importhandlers/controllers/input_parameters.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.importhandlers.xml.controllers.input_parameters'

    module 'app.datas.model'
    module 'app.testresults.model'
    module 'app.models.model'
    module 'app.datasets.model'
    module 'app.features.models'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null
  $q = null
  $rootScope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $scope = $rootScope.$new()
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')
    $q = $injector.get('$q')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'InputParameterTypesLoader', ->

    it 'should init scope', inject (InputParameter)->

      createController 'InputParameterTypesLoader', {InputParameter: InputParameter}

      expect($scope.types).toEqual ["boolean","integer","float","date","string"]


  describe 'InputParametersListCtrl', ->

    handler = null

    beforeEach inject (InputParameter, XmlImportHandler)->
      createController 'InputParametersListCtrl', {InputParameter: InputParameter}
      expect($scope.init).toBeDefined()
      expect($scope.add).toBeDefined()
      expect($scope.delete).toBeDefined()
      expect($scope.MODEL).toEqual InputParameter
      expect($scope.FIELDS).toEqual InputParameter.MAIN_FIELDS
      expect($scope.ACTION).toEqual 'loading input parameters'

    it 'should init scope with xml input parameters', inject (XmlImportHandler)->
      handler = new XmlImportHandler
        id: 999
        xml_input_parameters: {some: 'params'}
      $scope.init(handler)
      $scope.$digest()

      expect($scope.handler).toEqual handler
      expect($scope.kwargs).toEqual {'import_handler_id': handler.id}
      expect($scope.objects).toEqual handler.xml_input_parameters

      handler.xml_input_parameters = {other: 'parameters'}
      $scope.$digest()
      expect($scope.objects).toEqual handler.xml_input_parameters

    it 'should init scope with no xml input parameters', inject (XmlImportHandler)->
      handler = new XmlImportHandler
        id: 999
      $scope.init(handler)
      $scope.$digest()
      expect($scope.handler).toEqual handler
      expect($scope.kwargs).toEqual {'import_handler_id': handler.id}
      expect($scope.objects).toEqual []

    it 'should call openDialog to add', inject (InputParameter, XmlImportHandler)->
      handler = new XmlImportHandler
        id: 888
        xml_input_parameters: {some: 'params'}

      $scope.openDialog = jasmine.createSpy '$scope.openDialog'
      $scope.add(handler)
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: jasmine.any(InputParameter)
        template: 'partials/importhandlers/xml/input_parameters/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
        action: 'add input parameter'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
      expect($scope.openDialog.calls.mostRecent().args[1].model.import_handler_id).toEqual handler.id

    it 'should openDialog to delete', ->
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'
      param =
        some: 'params'
      $scope.delete(param)
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: param
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete input parameter'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
