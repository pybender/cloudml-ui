describe 'xml_importhandlers/controllers/datasources.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.importhandlers.xml.controllers.datasources'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null
  $rootScope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')

    $scope = $rootScope.$new()

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()


  describe 'DatasourcesTypesLoader', ->

    it 'should watch configurations', ->
      # starting with a configuration
      $scope.configuration = {type1: 't1', type2: 't2'}
      createController 'DatasourcesTypesLoader'
      $scope.$digest()
      expect($scope.types).toEqual ['type1', 'type2']

      # starting with on configuration
      delete $scope.configuration
      createController 'DatasourcesTypesLoader'
      $scope.$digest()
      expect($scope.types).toEqual []

      $scope.configuration = {type1: 't1', type2: 't2'}
      $scope.$digest()
      expect($scope.types).toEqual ['type1', 'type2']

      # changing configuuration
      $scope.configuration = {type1: 't1', type2: 't2', type3: 't3'}
      $scope.$digest()
      expect($scope.types).toEqual ['type1', 'type2', 'type3']


  describe 'DatasourcesListCtrl', ->

    beforeEach ->
      $rootScope.openDialog = (->)
      spyOn($rootScope, 'openDialog').and.returnValue {result: 'then': (->)}

    it 'should init scope and call unto openDialog when needed',
      inject (Datasource, XmlImportHandler)->
        createController 'DatasourcesListCtrl', {Datasource: Datasource}
        expect($scope.MODEL).toEqual = Datasource
        expect($scope.FIELDS).toEqual Datasource.MAIN_FIELDS
        expect($scope.ACTION).toEqual 'loading datasources'

        handler = new XmlImportHandler
          id: 888
          xml_data_sources: [
            id: 1
            name: 'ds1'
          ,
            id: 1
            name: 'ds1'
          ]
        $scope.init handler
        $scope.$digest()

        expect($scope.handler).toEqual handler
        expect($scope.kwargs).toEqual {'import_handler_id': handler.id}
        expect($scope.objects).toEqual handler.xml_data_sources

        # check the watch is working
        $scope.handler.xml_data_sources = [{id:4, name: 'ds4'}]
        $scope.$digest()
        expect($scope.objects).toEqual handler.xml_data_sources

        # add dialog
        $scope.add()
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any(Datasource)
          template: 'partials/importhandlers/xml/datasources/edit.html'
          ctrlName: 'ModelWithParamsEditDialogCtrl'
          action: 'add datasource'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        # edit dialog
        datasource = new Datasource {id: 777, name: 'ds777'}
        $scope.edit(datasource)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: datasource
          template: 'partials/importhandlers/xml/datasources/edit.html'
          ctrlName: 'ModelWithParamsEditDialogCtrl'
          action: 'edit datasource'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        # delete dialog
        $scope.delete(datasource)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: datasource
          template: 'partials/base/delete_dialog.html'
          ctrlName: 'DialogCtrl'
          action: 'delete datasource'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'XmlDataSourceSelectCtrl', ->

    it 'should init scope and load',
      inject (Datasource, XmlImportHandler)->
        $scope.openDialog = jasmine.createSpy '$scope.openDialog'
        createController 'XmlDataSourceSelectCtrl', {Datasource: Datasource}

        datasource = new Datasource {id: 444, name: 'ds444'}
        response = {}
        response[datasource.API_FIELDNAME + 's'] = [datasource]
        $httpBackend.expectGET("#{settings.apiUrl}xml_import_handlers/555/datasources/?import_handler_id=555&show=name&type=dataset+type")
        .respond 200, angular.toJson response

        $scope.init 555, 'dataset type'
        expect($scope.handler_id).toEqual 555
        expect($scope.ds_type).toEqual 'dataset type'
        $httpBackend.flush()

        expect($scope.datasources.length).toBe 1
        expect($scope.datasources[0].name).toEqual datasource.name
        expect($scope.datasources[0].id).toEqual datasource.id

        # error
        $scope.setError = jasmine.createSpy '$scope.setError'
        $httpBackend.expectGET("#{settings.apiUrl}xml_import_handlers/555/datasources/?import_handler_id=555&show=name&type=dataset+type")
        .respond 400

        $scope.init 555, 'dataset type'
        $httpBackend.flush()
        expect($scope.setError).toHaveBeenCalled()

