'use strict'

describe 'app.xml_importhandlers.controllers', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.xml_importhandlers.models'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.controllers'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  createController = null
  $scope = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')

    $scope = $rootScope.$new()
    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
  )


  describe 'XmlImportHandlerListCtrl', ->

    it 'should make no query and initialize fields', inject (XmlImportHandler)->
      createController 'XmlImportHandlerListCtrl', {XmlImportHandler: XmlImportHandler}

      expect($scope.MODEL).toEqual XmlImportHandler
      expect($scope.FIELDS).toEqual XmlImportHandler.MAIN_FIELDS
      expect($scope.ACTION).toEqual 'loading handler list'


  describe 'XmlImportHandlerDetailsCtrl', ->

    beforeEach ->
      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    prepareContext = (XmlImportHandler, sections, fields, failResponse)->
      handler = new XmlImportHandler {id: 999}
      $routeParams = {id: handler.id}
      createController 'XmlImportHandlerDetailsCtrl', {$routeParams: $routeParams}
      $scope.$broadcast = jasmine.createSpy '$scope.$broadcast'

      expect($scope.handler.id).toEqual handler.id
      expect($scope.LOADED_SECTIONS).toEqual []
      expect($scope.PROCESS_STRATEGIES).toEqual = _.sortBy XmlImportHandler.PROCESS_STRATEGIES, (s)-> s
      expect($scope.initSections).toHaveBeenCalledWith $scope.go

      response = {}
      response[handler.API_FIELDNAME] = handler
      if not failResponse
        $httpBackend.expectGET "#{handler.BASE_API_URL}#{handler.id}/?show=#{fields}"
        .respond 200, angular.toJson response
      else
        $httpBackend.expectGET "#{handler.BASE_API_URL}#{handler.id}/?show=#{fields}"
        .respond 400
      $scope.go sections
      $httpBackend.flush()

    it 'should raise error with no route paramter id', ->

      expect ->
        createController 'XmlImportHandlerDetailsCtrl'
      .toThrow new Error "Can't initialize without import handler id"

    it 'should initialize scope and load xml only', inject (XmlImportHandler)->

      prepareContext XmlImportHandler, ['something', 'xml'], 'xml', false

      expect($scope.LOADED_SECTIONS).toEqual ['something']
      expect($scope.$broadcast).not.toHaveBeenCalled()

    it 'should should handle errors', inject (XmlImportHandler)->

      prepareContext XmlImportHandler, ['something', 'xml'], 'xml', true

      expect($scope.LOADED_SECTIONS).toEqual []
      expect($scope.$broadcast).not.toHaveBeenCalled()
      expect($scope.setError.mostRecentCall.args[1]).toEqual 'loading handler details'

    it 'should initialize scope and load with all fields and broadcast', inject (XmlImportHandler)->

      prepareContext XmlImportHandler, ['dataset', 'something'],
        'id,name,created_on,created_by,xml_data_sources,xml_input_parameters,xml_scripts,entities,import_params,predict', false

      expect($scope.LOADED_SECTIONS).toEqual ['dataset']
      expect($scope.$broadcast).toHaveBeenCalledWith 'loadDataSet', true

    it 'should initialize scope and load with all fields and not broadcast dataset load', inject (XmlImportHandler)->

      prepareContext XmlImportHandler, ['main', 'something'],
        'id,name,created_on,created_by,xml_data_sources,xml_input_parameters,xml_scripts,entities,import_params,predict', false

      expect($scope.LOADED_SECTIONS).toEqual ['main']
      expect($scope.$broadcast).not.toHaveBeenCalled()


  describe 'AddXmlImportHandlerCtl', ->

    it 'should initialize scope', inject (XmlImportHandler)->

      createController 'AddXmlImportHandlerCtl', {XmlImportHandler: XmlImportHandler}

      expect($scope.types).toEqual [{name: 'Db'}, {name: 'Request'}]
      expect($scope.model).toEqual jasmine.any(XmlImportHandler)


  describe 'PredictCtrl', ->

    it 'should initialize scope', inject (XmlImportHandler)->

      createController 'PredictCtrl'

      handler = new XmlImportHandler {id: 888}
      expect($scope.init).toBeDefined()
      $scope.init handler

      expect($scope.handler).toEqual handler
      expect($scope.kwargs).toEqual {'import_handler_id': handler.id}

      # change predict
      predict =
        models: ['some', 'models']
        lable: 'predict label'
        probability: 0.05
      handler.predict = predict
      $scope.$digest()

      expect($scope.predict_models).toEqual predict.models
      expect($scope.predict).toEqual predict
      expect($scope.label).toEqual predict.label
      expect($scope.probability).toEqual predict.probability
