'use strict'

# jasmine specs for datasets

describe 'Features Controllers', ->

  beforeEach(module 'ngCookies')
  beforeEach(module 'ngRoute')
  beforeEach(module 'ui.bootstrap')

  beforeEach(module 'app.base')
  beforeEach(module 'app.config')
  beforeEach(module 'app.services')

  beforeEach(module 'app.features.models')
  beforeEach(module 'app.features.controllers.base')

  $httpBackend = null
  $scope = null
  settings = null
  $routeParams = null
  $window = null
  createController = null
  TRANSFORMERS = {configuration: {dictionary: defaults: {x: 1}}}
  originalLoadParameters = window.loadParameters

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $scope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $window = $injector.get('$window')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()
     window.loadParameters = originalLoadParameters

  describe 'ModelEditDialogCtrl', ->

    it 'should handler openOptions with model', ->
      openOptions =
        model:
          LIST_MODEL_NAME: 'some model name'
      createController 'ModelEditDialogCtrl', {openOptions: openOptions}
      expect($scope.model).toEqual openOptions.model
      expect($scope.LIST_MODEL_NAME).toEqual openOptions.model.LIST_MODEL_NAME
      expect($scope.DONT_REDIRECT).toBe true

    it 'should handle openOptions with no model', ->
      openOptions =
        extra:
          handler:
            some_field:
              some: 'object'
          fieldname: 'some_field'
        list_model_name: 'some list model name'

      createController 'ModelEditDialogCtrl', {openOptions: openOptions}
      expect($scope.model).toEqual openOptions.extra.handler.some_field
      expect($scope.LIST_MODEL_NAME).toEqual openOptions.list_model_name
      expect($scope.DONT_REDIRECT).toBe true

    it 'should throw error', ->
      expect ->
        createController 'ModelEditDialogCtrl', {openOptions: {}}
      .toThrow new Error "Please specify a model or handler and fieldname"

    it 'should handle SaveObjectCtl:save:success event', ->
      openOptions =
        model:
          LIST_MODEL_NAME: 'some model name'
      $scope.$close = jasmine.createSpy '$scope.$close'
      createController 'ModelEditDialogCtrl', {openOptions: openOptions}
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($scope.$close).toHaveBeenCalledWith true


  describe 'ModelWithParamsEditDialogCtrl', ->

    it 'should handle openOptions with model (transformer) and loading parameters',
      inject (Transformer)->
        openOptions =
          model:
            new Transformer
              id: 123321
              name: 'transformer name'
              type: 'dictionary'
              params: {x: 1, y: 2}
              LIST_MODEL_NAME: 'list model name'

        prepareTestContext = (failGET) ->
          if not failGET
            $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{openOptions.model.id}/action/configuration/")
            .respond 200, angular.toJson(TRANSFORMERS)
          else
            $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{openOptions.model.id}/action/configuration/")
            .respond 400

          window.loadParameters = jasmine.createSpy('loadParameters')
          $scope.setError = jasmine.createSpy '$scope.setError'
          createController 'ModelWithParamsEditDialogCtrl', {openOptions: openOptions}
          $httpBackend.flush()

        prepareTestContext(false)
        expect($scope.model).toEqual openOptions.model
        expect($scope.LIST_MODEL_NAME).toEqual openOptions.model.LIST_MODEL_NAME
        expect($scope.DONT_REDIRECT).toBe true
        expect($scope.params).toEqual {}
        expect($scope.configuration).toEqual TRANSFORMERS.configuration
        expect(window.loadParameters).toHaveBeenCalledWith openOptions.model, $scope.configuration, false
        expect($scope.setError).not.toHaveBeenCalled()

        prepareTestContext(true)
        expect($scope.setError).toHaveBeenCalled()

    it 'should handle openOptions with extra (feature) and loading parameters',
      inject (Transformer)->
        openOptions =
          extra:
            feature:
              some_field:
                new Transformer
                  id: 123321
                  name: 'transformer name'
                  type: 'dictionary'
                  params: {x: 1, y: 2}
            fieldname: 'some_field'
          list_model_name: 'list model name'

        TRANSFORMERS = {configuration: {dictionary: defaults: {x: 1}}}

        $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{openOptions.extra.feature.some_field.id}/action/configuration/")
        .respond 200, angular.toJson(TRANSFORMERS)

        window.loadParameters = jasmine.createSpy('loadParameters')
        createController 'ModelWithParamsEditDialogCtrl', {openOptions: openOptions}
        $httpBackend.flush()
        expect($scope.feature).toEqual openOptions.extra.feature
        expect($scope.model).toEqual openOptions.extra.feature.some_field
        expect($scope.LIST_MODEL_NAME).toEqual openOptions.list_model_name
        expect($scope.DONT_REDIRECT).toBe true
        expect($scope.params).toEqual {}
        expect($scope.configuration).toEqual TRANSFORMERS.configuration
        expect(window.loadParameters).toHaveBeenCalledWith openOptions.extra.feature.some_field,
          $scope.configuration, false

    it 'should handle openOptions with extra (model) and loading parameters',
      inject (Transformer)->
        openOptions =
          extra:
            model:
              some_field:
                new Transformer
                  id: 123321
                  name: 'transformer name'
                  type: 'dictionary'
                  params: {x: 1, y: 2}
            fieldname: 'some_field'
          list_model_name: 'list model name'

        TRANSFORMERS = {configuration: {dictionary: defaults: {x: 1}}}

        $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{openOptions.extra.model.some_field.id}/action/configuration/")
        .respond 200, angular.toJson(TRANSFORMERS)

        window.loadParameters = jasmine.createSpy('loadParameters')
        createController 'ModelWithParamsEditDialogCtrl', {openOptions: openOptions}
        $httpBackend.flush()
        expect($scope.target_model).toEqual openOptions.extra.model
        expect($scope.model).toEqual openOptions.extra.model.some_field
        expect($scope.LIST_MODEL_NAME).toEqual openOptions.list_model_name
        expect($scope.DONT_REDIRECT).toBe true
        expect($scope.params).toEqual {}
        expect($scope.configuration).toEqual TRANSFORMERS.configuration
        expect(window.loadParameters).toHaveBeenCalledWith openOptions.extra.model.some_field,
          $scope.configuration, false

    it 'should throw error', ->
      expect ->
        createController 'ModelWithParamsEditDialogCtrl', {openOptions: {}}
      .toThrow new Error "Please specify a model or feature and field name"

    it 'should handle SaveObjectCtl:save:success event', ->
      openOptions =
        model:
          $getConfiguration: ->
            {then: ()->}
      $scope.$close = jasmine.createSpy '$scope.$close'
      createController 'ModelWithParamsEditDialogCtrl', {openOptions: openOptions}
      $scope.$emit 'SaveObjectCtl:save:success'
      $scope.$digest()
      expect($scope.$close).toHaveBeenCalledWith true


  describe 'ConfigurationLoaderCtrl', ->

    it 'should', inject (Feature, Transformer)->
      feature = new Feature
        id: 123321
        name: 'feature name'
        feature_set_id: 1
        transformer:
          new Transformer
            id: 123321
            name: 'transformer name'
            type: 'dictionary'
            params: {x: 1, y: 2}

      prepareTestContext = (failGET) ->
        if not failGET
          $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{feature.transformer.id}/action/configuration/")
          .respond 200, angular.toJson(TRANSFORMERS)
        else
          $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{feature.transformer.id}/action/configuration/")
          .respond 400

        window.loadParameters = jasmine.createSpy('loadParameters')
        $scope.setError = jasmine.createSpy '$scope.setError'
        createController 'ConfigurationLoaderCtrl'
        $scope.init feature, 'transformer'
        $httpBackend.flush()

      prepareTestContext(false)
      expect($scope.parentModel).toEqual feature
      expect($scope.fieldname).toEqual 'transformer'
      expect($scope.configuration).toEqual TRANSFORMERS.configuration
      expect($scope.configurationLoaded).toBe true
      expect(window.loadParameters).toHaveBeenCalledWith feature.transformer,
        $scope.configuration, false
      expect($scope.setError).not.toHaveBeenCalled()
      # configuration loaded should not GET configurations
      $scope.loadConfiguration(transformer)

      # ensure the watch ticks :)
      transformer = feature.transformer
      feature.transformer = null
      $scope.$digest()

      $httpBackend.expectGET("#{settings.apiUrl}features/transformers/#{transformer.id}/action/configuration/")
      .respond 200, angular.toJson(TRANSFORMERS)
      feature.transformer = transformer
      $scope.$digest()
      $httpBackend.flush()

      prepareTestContext(true)
      expect($scope.setError).toHaveBeenCalled()


  describe 'loadParameters', ->

    it 'should handle models with no types', ->
      model = {}
      window.loadParameters model
      expect(model.params).toEqual {}

    it 'should handle models with a type and load the configuration with no defaults', ->
      model =
        type: 'dictionary'
        params: {x: 1, y: 2}
      configuration =
        dictionary:
          defaults: {a: 1, b: 2}

      window.loadParameters model, configuration
      expect(model.config).toEqual configuration.dictionary
      expect(model.params).toEqual {x: 1, y: 2}

    it 'should handle models with a type and load the configuration with no defaults and no params', ->
      model =
        type: 'dictionary'
      configuration =
        dictionary:
          defaults: {a: 1, b: 2}

      window.loadParameters model, configuration
      expect(model.config).toEqual configuration.dictionary
      expect(model.params).toEqual {}

    it 'should handle models with a type and load the configuration with defaults', ->
      model =
        type: 'dictionary'
        params: {x: 1, y: 2}
      configuration =
        dictionary:
          defaults: {a: 1, b: 2}

      window.loadParameters model, configuration, true
      expect(model.config).toEqual configuration.dictionary
      expect(model.params).toEqual {a: 1, b: 2}


