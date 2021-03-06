'use strict'

describe 'app.features.controllers', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.features.controllers'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  createController = null
  $scope = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')

    $rootScope.openDialog = (->)
    spyOn($rootScope, 'openDialog').and.returnValue {result: 'then': (->)}

    $scope = $rootScope.$new()
    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()


  describe 'FeaturesSetListCtrl', ->

    it 'should make no query and initialize fields', inject (FeaturesSet)->
      createController 'FeaturesSetListCtrl'

      expect($scope.MODEL).toEqual FeaturesSet
      expect($scope.FIELDS).toEqual FeaturesSet.MAIN_FIELDS
      expect($scope.ACTION).toEqual 'loading feature sets'
      expect($scope.add).toEqual jasmine.any(Function)

    it 'should call on to open add feature dialog', inject (FeaturesSet)->

      createController 'FeaturesSetListCtrl'

      $scope.add()
      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: jasmine.any FeaturesSet
        template: 'partials/features/sets/add.html'
        ctrlName: 'AddFeatureSetDialogCtrl'
        action: 'add feature set'
        list_model_name: "FeaturesSets"
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'FeaturesSetDetailsCtrl', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should init and watch modelObj.featuresSet for changes', inject (FeaturesSet)->

      createController 'FeaturesSetDetailsCtrl'

      model = {id: 111, name: 'some_model'}

      $scope.init model

      expect($scope.modelObj).toEqual model

      # now change featuresSet on model
      featuresSet = new FeaturesSet {id: 222}
      model.featuresSet = featuresSet
      response = {}
      response[featuresSet.API_FIELDNAME + 's'] = featuresSet
      $httpBackend.expectGET "#{featuresSet.BASE_API_URL}#{featuresSet.id}/?show=id,schema_name,features_count,target_variable,group_by"
      .respond 200, angular.toJson response
      $scope.$digest()
      $httpBackend.flush()

      expect($scope.featuresSet).toEqual featuresSet

      # changing again will do nothing !!! which is strange
      newFeaturesSet = new FeaturesSet {id: 333}
      model.featuresSet = newFeaturesSet
      $scope.$digest()

      expect($scope.featuresSet).toEqual featuresSet

    it 'should init and handle http error', inject (FeaturesSet)->

      createController 'FeaturesSetDetailsCtrl'

      model = {id: 111, name: 'some_model'}

      $scope.init model

      expect($scope.modelObj).toEqual model

      # now change featuresSet on model
      featuresSet = new FeaturesSet {id: 222}
      model.featuresSet = featuresSet
      $httpBackend.expectGET "#{featuresSet.BASE_API_URL}#{featuresSet.id}/?show=id,schema_name,features_count,target_variable,group_by"
      .respond 400
      $scope.$digest()
      $httpBackend.flush()

      expect($scope.featuresSet).toBeUndefined()
      expect($scope.setError.calls.argsFor(0)[1]).toEqual 'loading featuresSet'

    it 'should call on open dialog to add feature', inject (FeaturesSet)->

      createController 'FeaturesSetDetailsCtrl'

      $scope.featuresSet = new FeaturesSet
      $scope.addFeature()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: $scope.featuresSet
        template: 'partials/features/items/add.html'
        ctrlName: 'AddFeatureDialogCtrl'
        action: 'add feature'
        path: "feature"
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


  describe 'FeaturesListCtrl', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should make no query and initialize fields', inject (Feature)->
      createController 'FeaturesListCtrl'

      expect($scope.MODEL).toEqual Feature
      expect($scope.FIELDS).toEqual Feature.MAIN_FIELDS
      expect($scope.ACTION).toEqual 'loading features'

    it 'should init and watch modelObj.features_set_id for changes', ->

      createController 'FeaturesListCtrl'

      model = {id: 111, name: 'some_model'}

      $scope.init model

      expect($scope.modelObj).toEqual model

      $scope.modelObj.features_set_id = 10
      $scope.$digest()
      expect($scope.filter_opts).toEqual {'feature_set_id': 10}

      # we are watching value, beware
      $scope.modelObj.features_set_id = 12
      $scope.$digest()
      expect($scope.filter_opts).toEqual {'feature_set_id': 12}


  describe 'GroupBySelector', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should initialize fields and update features set of model on watch', inject (FeaturesSet) ->
      createController 'GroupBySelector'

      expect($scope.group_by_opts).toEqual
        multiple: true,
        query: jasmine.any Function
      expect($scope.updateGroupBy).toEqual jasmine.any(Function)
      expect($scope.clear).toEqual jasmine.any(Function)

      # trigger some events
      $scope.objects = [{id: 111, name: 'feature111'},
        {id: 222, name: 'feature222'}, {id: 333, name: 'feature333'}]
      featuresSet = new FeaturesSet {id: 111, name: 'set111', group_by: []}
      $scope.modelObj = {featuresSet: featuresSet}
      $scope.$digest()
      expect($scope.modelObj.featuresSet.group_by).toEqual []

      $scope.modelObj.featuresSet.group_by = '111,333'
      response = {}
      response[featuresSet.API_FIELDNAME] = $scope.modelObj.featuresSet
      $httpBackend.expectPUT "#{featuresSet.BASE_API_URL}#{featuresSet.id}/"
      .respond 200, angular.toJson response
      $scope.$digest()
      expect($scope.modelObj.featuresSet.group_by).toEqual [
        {id: 111, name: 'feature111'}, {id: 333, name: 'feature333'}]
      $httpBackend.flush()

      $scope.modelObj.featuresSet.group_by = '222,zzz'
      response = {}
      response[featuresSet.API_FIELDNAME] = $scope.modelObj.featuresSet
      $httpBackend.expectPUT "#{featuresSet.BASE_API_URL}#{featuresSet.id}/"
      .respond 200, angular.toJson response
      $scope.$digest()
      expect($scope.modelObj.featuresSet.group_by).toEqual [{id: 222, name: 'feature222'}]
      $httpBackend.flush()

    it 'should handle group by commands from select2', ->

      createController 'GroupBySelector'

      callbackFn = jasmine.createSpy '$scope.group_by_opts.query'
      $scope.objects = [{id: 111, name: 'name111'}, {id: 222, name: 'name222'}]
      $scope.group_by_opts.query {callback: callbackFn}

      expect(callbackFn).toHaveBeenCalledWith {results: [{id: 111, text: 'name111'}, {id: 222, text: 'name222'}]}

    it 'updating the group and handling http errors', inject (FeaturesSet, $timeout)->

      createController 'GroupBySelector'

      featuresSet = new FeaturesSet {id: 111, name: 'set111'}
      $scope.modelObj = {featuresSet: featuresSet}

      response = {}
      response[featuresSet.API_FIELDNAME] = featuresSet
      $httpBackend.expectPUT "#{featuresSet.BASE_API_URL}#{featuresSet.id}/"
      .respond 200, angular.toJson response

      $scope.updateGroupBy()
      $httpBackend.flush()

      expect($rootScope.segmentationMsg).toEqual 'Group by fields have been saved'
      $timeout.flush()
      expect($rootScope.segmentationMsg).toBe null

      # handling http errors
      $httpBackend.expectPUT "#{featuresSet.BASE_API_URL}#{featuresSet.id}/"
      .respond 400

      $scope.updateGroupBy()
      $httpBackend.flush()

      expect($rootScope.segmentationMsg).toBe null
      expect($scope.setError.calls.argsFor(0)[1]).toEqual 'saving group by fields'


  describe 'AddFeatureTypeCtrl', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should make no query and initialize fields', inject (NamedFeatureType)->
      createController 'AddFeatureTypeCtrl'

      expect($scope.model).toEqual jasmine.any(NamedFeatureType)
      expect($scope.types).toEqual NamedFeatureType.$TYPES_LIST


  describe 'FeatureActionsCtrl', ->

    model = null
    feature = null
    beforeEach inject (Feature)->
      model = {id: 123, name: 'model123'}
      feature = new Feature {id: 999, name: 'feature_name', is_required: false, feature_set_id: 888}
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should initialize scope with model or throw exception', ->
      createController 'FeatureActionsCtrl'
      expect($scope.init).toEqual jasmine.any(Function)

      expect ->
        $scope.init {}
      .toThrow new Error 'Please specify feature model'

      expect ->
        $scope.init null
      .toThrow new Error 'Please specify feature model'

      $scope.init {model: model}
      expect($scope.model).toEqual model

    it 'should call unto openDialog to delete a feature', ->
      createController 'FeatureActionsCtrl'
      expect($scope.deleteModel).toEqual jasmine.any(Function)

      $scope.deleteModel(model)

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete feature'
        list_model_name: 'features'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should toggle feature is_required and handle http errors', ->
      createController 'FeatureActionsCtrl'
      expect($scope.makeRequired).toEqual jasmine.any(Function)
      $scope.$emit = jasmine.createSpy '$scope.$emit'

      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.makeRequired feature, true
      $httpBackend.flush()

      expect($scope.$emit).toHaveBeenCalledWith 'updateList', []

      # error handling
      $httpBackend.expectPUT ""
      .respond 400
      $scope.makeRequired feature, true
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'updating feature'

    it 'should toggle feature disabled and handle http errors', ->
      createController 'FeatureActionsCtrl'
      expect($scope.makeRequired).toEqual jasmine.any(Function)
      $scope.$emit = jasmine.createSpy '$scope.$emit'

      scaler = {type: 'scaler type'}
      transformer = {type: 'transformer type'}
      feature.disabled = true
      feature.scaler = scaler
      feature.transformer = transformer
      response = {}
      response[feature.API_FIELDNAME] = {"feature": {"id": 999, "name": "feature_name"}}
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.toggleFeatureDisabled feature
      $httpBackend.flush()
      expect(feature.disabled).toBe false
      expect(feature.scaler).toEqual scaler
      expect(transformer).toEqual transformer

      expect($scope.$emit).toHaveBeenCalledWith 'updateList', []

      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.toggleFeatureDisabled feature
      $httpBackend.flush()
      expect(feature.disabled).toBe true
      expect(feature.scaler).toEqual scaler
      expect(transformer).toEqual transformer

      expect($scope.$emit).toHaveBeenCalledWith 'updateList', []

      # error handling
      feature.disabled = true
      $httpBackend.expectPUT ""
      .respond 400
      $scope.toggleFeatureDisabled feature
      $httpBackend.flush()
      expect(feature.disabled).toBe true

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'updating feature'

    it 'should make a feature as a target', inject (NamedFeatureType)->
      createController 'FeatureActionsCtrl'
      expect($scope.makeTarget).toEqual jasmine.any(Function)
      $scope.$emit = jasmine.createSpy '$scope.$emit'

      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.makeTarget feature
      $httpBackend.flush()

      expect($scope.$emit).toHaveBeenCalledWith 'modelChanged', []
      expect(feature.is_target_variable).toBe true

      # the scope has a featureset
      $scope.featuresSet = {target_variable: null}

      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.makeTarget feature
      $httpBackend.flush()

      expect($scope.featuresSet.target_variable).toEqual feature.name

      # error handling
      $httpBackend.expectPUT ""
      .respond 400
      $scope.makeTarget feature
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'updating feature'

    it 'should call unto openDialog to edit scalar', ->
      createController 'FeatureActionsCtrl'
      expect($scope.editScaler).toEqual jasmine.any(Function)

      $scope.editScaler(feature)

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: feature
        template: 'partials/features/scalers/edit_feature_scaler.html'
        ctrlName: 'DialogCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should call unto openDialog to edit transformer', ->
      createController 'FeatureActionsCtrl'
      expect($scope.editTransformer).toEqual jasmine.any(Function)

      $scope.editTransformer(feature)

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: feature
        template: 'partials/features/transformers/edit_feature_transformer.html'
        ctrlName: 'DialogCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should delete transformer', inject (Transformer)->
      createController 'FeatureActionsCtrl'
      expect($scope.deleteTransformer).toEqual jasmine.any(Function)

      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.deleteTransformer feature
      $httpBackend.flush()

      expect(feature.remove_transformer).toEqual true
      expect(feature.transformer).toEqual jasmine.any(Transformer)

      # handles errors
      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 400
      $scope.deleteTransformer feature
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error while removing transformer'

    it 'should delete scalar', inject (Scaler)->
      createController 'FeatureActionsCtrl'
      expect($scope.deleteScaler).toEqual jasmine.any(Function)

      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 200, angular.toJson response
      $scope.deleteScaler feature
      $httpBackend.flush()

      expect(feature.remove_scaler).toEqual true
      expect(feature.scaler).toEqual jasmine.any(Scaler)

      # handles errors
      response = {}
      response[feature.API_FIELDNAME] = feature
      $httpBackend.expectPUT "#{feature.BASE_API_URL}#{feature.id}/"
      .respond 400
      $scope.deleteScaler feature
      $httpBackend.flush()

      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'error while removing scaler'
