'use strict'

# jasmine specs for datasets

describe 'importhandlers/controllers/datasources.coffee', ->

  beforeEach(module 'ngCookies')

  beforeEach(module 'app.base')
  beforeEach(module 'app.config')
  beforeEach(module 'app.services')

  beforeEach(module 'app.importhandlers.model')
  beforeEach(module 'app.importhandlers.controllers.datasources')

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $scope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')

    createController = (ctrl, extras) ->
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
      $scope.setError = jasmine.createSpy('$scope.setError').andReturn('an error')
      createController 'DataSourcesSelectLoader', {DataSource: DataSource}
      $httpBackend.flush()

      expect($scope.datasources).toEqual []
      expect($scope.err).toEqual 'an error'
      expect($scope.setError).toHaveBeenCalled()

  describe 'DataSourceListCtrl', ->

    it 'should load prepare $scope', inject (DataSource)->
      createController 'DataSourceListCtrl', {DataSource: DataSource}
      $scope.openDialog = jasmine.createSpy '$scope.openDialog'

      expect($scope.MODEL).toEqual DataSource
      expect($scope.FIELDS).toEqual DataSource.MAIN_FIELDS
      expect($scope.ACTION).toBeDefined()
      expect($scope.LIST_MODEL_NAME).toEqual DataSource.LIST_MODEL_NAME

      $scope.edit({some: 'ds'})
      expect($scope.openDialog).toHaveBeenCalledWith
        model: {some: 'ds'}
        template: 'partials/import_handler/datasource/edit.html'
        ctrlName: 'ModelEditDialogCtrl'

      $scope.add()
      obj = $scope.openDialog.mostRecentCall.args[0]
      expect(obj.template).toEqual 'partials/import_handler/datasource/add.html'
      expect(obj.ctrlName).toEqual 'ModelEditDialogCtrl'
      expect(obj.model).toBeDefined()

      $scope.delete({some: 'ds'})
      expect($scope.openDialog).toHaveBeenCalledWith
        model: {some: 'ds'}
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete data source'

  describe 'DataSourceEditDialogCtrl', ->

    it 'should load prepare $scope', inject (ImportHandler)->
      openOptions =
        extra:
          handler: new ImportHandler({id:123321, name: 'handler'})
          ds: {some: 'ds'}

      $scope.$close = jasmine.createSpy '$scope.$close'
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

      # with errror
      $scope.setError = jasmine.createSpy '$scope.setError'
      $httpBackend.expectGET("#{settings.apiUrl}importhandlers/123321/?show=data")
      .respond 400
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalled()
