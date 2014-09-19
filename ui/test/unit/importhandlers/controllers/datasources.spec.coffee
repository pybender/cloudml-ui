'use strict'

# jasmine specs for datasets

describe 'importhandlers/controllers/datasources.coffee', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.model'
    module 'app.importhandlers.controllers.datasources'

  $httpBackend = null
  $scope = null
  $rootScope = null
  settings = null
  $window = null
  createController = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')

    createController = (ctrl, extras) ->
      $scope = $rootScope.$new()
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()

  describe 'DataSourceChoicesLoader', ->

    it 'should add type and vendors to scope', inject (DataSource)->
      createController 'DataSourceChoicesLoader', {DataSource: DataSource}
      expect($scope.types).toEqual DataSource.$TYPES_LIST
      expect($scope.vendors).toEqual DataSource.$VENDORS_LIST

  describe 'DataSourcesSelectLoader', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy('$rootScope.setError').and.returnValue 'an error'

    it 'should load datasources', inject (DataSource)->
      objects = [
        id: 1
        name: 'ds1'
      ,
        id: 2
        name: 'ds2'
      ]
      $httpBackend.expectGET("#{settings.apiUrl}datasources/?show=name,id")
      .respond 200, angular.toJson({predefined_data_sources: objects})
      createController 'DataSourcesSelectLoader', {DataSource: DataSource}
      $httpBackend.flush()

      expect($scope.datasources).toEqual objects

      # handling errors
      $httpBackend.expectGET("#{settings.apiUrl}datasources/?show=name,id")
      .respond 400
      $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue('an error')
      createController 'DataSourcesSelectLoader', {DataSource: DataSource}
      $httpBackend.flush()

      expect($scope.datasources).toEqual []
      expect($scope.err).toEqual 'an error'
      expect($scope.setError).toHaveBeenCalled()

  describe 'DataSourceListCtrl', ->

    beforeEach ->
      $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should prepare load datasource and handle errors', inject (DataSource)->
      # will just do nothing
      createController 'DataSourceListCtrl', {DataSource: DataSource}

      # success will call $scope.edit which opens the dialog
      ds = new DataSource {id: 999}
      response = []
      response[ds.API_FIELDNAME] = ds
      $httpBackend.expectGET "#{ds.BASE_API_URL}#{ds.id}/?show=name,id,type,db,created_on,created_by"
      .respond 200, angular.toJson response
      $routeParams = {id: ds.id}
      createController 'DataSourceListCtrl',
        $routeParams: $routeParams
        DataSource: DataSource
      $httpBackend.flush()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: jasmine.any DataSource
        template: 'partials/import_handler/datasource/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
      expect($scope.openDialog.calls.mostRecent().args[1].model.id).toEqual 999

      # error in http will call setError
      $httpBackend.expectGET "#{ds.BASE_API_URL}#{ds.id}/?show=name,id,type,db,created_on,created_by"
      .respond 400
      $routeParams = {id: ds.id}
      createController 'DataSourceListCtrl',
        $routeParams: $routeParams
        DataSource: DataSource
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading datasource details'

    it 'should prepare $scope functions', inject (DataSource)->
      createController 'DataSourceListCtrl', {DataSource: DataSource}

      expect($scope.MODEL).toEqual DataSource
      expect($scope.FIELDS).toEqual DataSource.MAIN_FIELDS
      expect($scope.ACTION).toBeDefined()
      expect($scope.LIST_MODEL_NAME).toEqual DataSource.LIST_MODEL_NAME

      $scope.edit({some: 'ds'})
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'ds'}
        template: 'partials/import_handler/datasource/edit.html'
        ctrlName: 'ModelEditDialogCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

      $scope.add()
      obj = $scope.openDialog.calls.mostRecent().args[1]
      expect(obj.template).toEqual 'partials/import_handler/datasource/add.html'
      expect(obj.ctrlName).toEqual 'ModelEditDialogCtrl'
      expect(obj.model).toBeDefined()

      $scope.delete({some: 'ds'})
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: {some: 'ds'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete data source'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

  describe 'DataSourceEditDialogCtrl', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'

    it 'should load prepare $scope', inject (ImportHandler)->
      openOptions =
        extra:
          handler: new ImportHandler({id:123321, name: 'handler'})
          ds: {some: 'ds'}

      createController 'DataSourceEditDialogCtrl', {openOptions: openOptions}

      expect($scope.handler).toEqual openOptions.extra.handler
      expect($scope.model).toEqual openOptions.extra.ds
      expect($scope.DONT_REDIRECT).toBe true

      response = {}
      response[ImportHandler.API_FIELDNAME] = []
      $httpBackend.expectGET("#{settings.apiUrl}importhandlers/123321/?show=data")
      .respond 200, angular.toJson(response)
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      $httpBackend.flush()
      expect($scope.$close).toHaveBeenCalledWith true

      # with errror
      $scope.$close.calls.reset()
      $httpBackend.expectGET("#{settings.apiUrl}importhandlers/123321/?show=data")
      .respond 400
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading datasource details'
      #expect($scope.$close).not.toHaveBeenCalled()
