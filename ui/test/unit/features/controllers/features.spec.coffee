describe 'features/controllers/features.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.datasets.model'
    module 'app.features.models'
    module 'app.features.controllers.features'
    spyOn(window, 'FormData').and.returnValue new ()->
      _data = {}
      return {
      append: (key, value)->
        _data[key] = value
      getData: ->
        return angular.copy(_data)
      toString: ->
        angular.toJson(_data)
      }


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

  prepareTestContext = (Model, Feature, Transformer, Scaler, Parameters, model_id, set_id, feature_id)->
    feature = new Feature
      id: feature_id
      feature_set_id: set_id
      name: 'feature'
      type: 'categorical'
      params: angular.toJson({})
    featureLoadResponse = {}
    featureLoadResponse[feature.API_FIELDNAME] = feature
    $httpBackend.expectGET("#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/?show=#{Feature.MAIN_FIELDS}")
    .respond 200, angular.toJson featureLoadResponse

    parameters = new Parameters
    parametersUrl = "#{parameters.BASE_API_URL}/"
    configuration = JSON.parse(map_url_to_response(parametersUrl, 'load parameters configuration')[1]).configuration
    expect(_.keys(configuration).length).toEqual 3
    expect(_.keys(configuration.params).length).toEqual 5
    expect(_.keys(configuration.defaults).length).toEqual 1
    expect(_.keys(configuration.types).length).toEqual 11

    $httpBackend.expectGET("#{parameters.BASE_API_URL}/")
    .respond.apply @, map_url_to_response(parametersUrl, 'load parameters configuration')

    createController 'FeatureEditCtrl',
      $routeParams: {model_id: model_id, set_id: set_id, feature_id: feature_id}
      $location: $location
      Model: Model
      Feature: Feature
      Transformer: Transformer
      Scaler: Scaler
      Parameters: Parameters
    $httpBackend.flush()

    return [configuration, feature]

  describe 'FeatureEditCtrl', ->

    it 'should error when route params model_id or set_id is not set',
      inject (Model, Feature, Transformer, Scaler, Parameters)->
        expect ->
          createController 'FeatureEditCtrl',
            $routeParams: {}
            $location: $location
            Model: Model
            Feature: Feature
            Transformer: Transformer
            Scaler: Scaler
            Parameters: Parameters
        .toThrow new Error 'Specify model id'

        expect ->
          createController 'FeatureEditCtrl',
            $routeParams: {model_id: 111}
            $location: $location
            Model: Model
            Feature: Feature
            Transformer: Transformer
            Scaler: Scaler
            Parameters: Parameters
        .toThrow new Error 'Specify set id'

    it 'should init scope properly with everything',
      inject (Model, Feature, Transformer, Scaler, Parameters)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        [configuration, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        expect($scope.modelObj).toEqual jasmine.any(Model)
        expect($scope.modelObj.id).toEqual model_id

        expect($scope.feature).toEqual jasmine.any(Feature)
        expect($scope.feature.id).toEqual feature_id
        expect($scope.feature.feature_set_id).toEqual set_id
        expect($scope.feature.transformer).toEqual jasmine.any(Transformer)
        expect($scope.feature.scaler).toEqual jasmine.any(Scaler)
        expect($scope.feature.params).toEqual '{}'
        expect($scope.feature.paramsDict).toEqual {split_pattern : null, min_df: null }

        expect($scope.configuration).toEqual configuration

    it 'should update paramsDict when type changes',
      inject (Model, Feature, Transformer, Scaler, Parameters)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        prepareTestContext Model, Feature, Transformer, Scaler,
          Parameters, model_id, set_id, feature_id

        # it is categorical by default
        $scope.feature.paramsDict.min_df = 5
        $scope.feature.paramsDict.split_pattern = 'zinger'
        $scope.feature.type = 'categorical_label'
        $scope.$digest()
        expect($scope.feature.paramsDict).toEqual {min_df: 5, split_pattern: 'zinger'}

        $scope.feature.type = 'composite'
        $scope.$digest()
        expect($scope.feature.paramsDict).toEqual {chain: null}

        $scope.feature.type = 'categorical'
        $scope.$digest()
        expect($scope.feature.paramsDict).toEqual {min_df: null, split_pattern: null}

  describe 'saving feature', ->

    it 'should handle feature type parameters',
      inject (Model, Feature, Transformer, Scaler, Parameters, $filter)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        [configuration, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        paramsDict = {min_df: 10, split_pattern: 'zozo'}
        updatedFeature = new Feature
          id: feature_id
          feature_set_id: set_id
          name: 'feature'
          type: 'categorical_label'
          params: angular.toJson(paramsDict)
          transformer: new Transformer({})
          scaler: new Scaler({})

        $httpBackend.expectPUT "#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/"
        , (data)->
          featureData = data.getData()
          params = JSON.parse featureData['params']
          valid = true
          valid = valid and featureData['name'] is 'feature'
          valid = valid and featureData['type'] is 'categorical_label'
          valid = valid and featureData['feature_set_id'] is 222
          valid = valid and featureData['is_target_variable'] is false
          valid = valid and params['min_df'] is paramsDict.min_df
          valid = valid and params['split_pattern'] is paramsDict.split_pattern

          valid = valid and featureData['remove_transformer'] is true
          valid = valid and 'transformer-predefined_selected' not in _.keys(featureData)
          valid = valid and 'transformer-params' not in _.keys(featureData)
          valid = valid and 'transformer-type' not in _.keys(featureData)
          valid = valid and 'transformer-transformer' not in _.keys(featureData)

          valid = valid and featureData['remove_scaler'] is true
          valid = valid and 'scaler' not in _.keys(featureData)

          if not valid
            console.log 'the post form was not as expected', data.getData()
          return valid
        .respond 200, angular.toJson({feature: updatedFeature})

        $scope.feature.type = 'categorical_label'
        $scope.feature.paramsDict = paramsDict
        $scope.feature.transformer.id = 0 # denotes removing transformer
        $scope.feature.scaler.id = 0      # denotes removing scaler
        $scope.$digest()

        $scope.save(['name', 'type', 'input_format', 'transformer', 'params', 'required', 'scaler__predefined_selected', 'scaler__name','scaler__type', 'scaler__params', 'default', 'feature_set_id', 'is_target_variable'])
        $httpBackend.flush()
        $scope.$digest()

        expect($scope.savingProgress).toEqual '100%'
        expect($location.url()).toEqual "/models/#{model_id}?action=model:details"
        expect($scope.feature.type).toEqual 'categorical_label'
        expect($scope.feature.paramsDict).toEqual paramsDict
        expect($scope.feature.params).toEqual angular.toJson(paramsDict)

    it 'should handle built in transformer',
      inject (Model, Feature, Transformer, Scaler, Parameters, $filter)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        [configuration, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        updatedFeature = new Feature
          id: feature_id
          feature_set_id: set_id
          name: 'feature'
          type: 'boolean'
          params: {}
          transformer: new Transformer({type: 'Dictionary', params: {'transformer': 'parameters'}})
          scaler: new Scaler({})

        $httpBackend.expectPUT "#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/"
        , (data)->
          featureData = data.getData()
          params = JSON.parse featureData['params']
          valid = true
          valid = valid and featureData['name'] is 'feature'
          valid = valid and featureData['type'] is 'boolean'
          valid = valid and featureData['feature_set_id'] is 222
          valid = valid and featureData['is_target_variable'] is false
          valid = valid and featureData['params'] is $filter('json')({})

          valid = valid and featureData['remove_transformer'] is false
          valid = valid and featureData['transformer-predefined_selected'] is false
          valid = valid and featureData['transformer-params'] is angular.toJson({'transformer': 'parameters'})
          valid = valid and featureData['transformer-type'] is 'Dictionary'
          valid = valid and 'transformer-transformer' not in _.keys(featureData)

          valid = valid and featureData['remove_scaler'] is true
          valid = valid and 'scaler' not in _.keys(featureData)

          if not valid
            console.log 'the post form was not as expected', data.getData()
          return valid
        .respond 200, angular.toJson({feature: updatedFeature})

        $scope.feature.type = 'boolean'
        $scope.feature.transformer.id = -1 # denotes built in transformer
        $scope.feature.transformer.type = 'Dictionary'
        $scope.feature.transformer.params = {'transformer': 'parameters'}
        $scope.feature.scaler.id = 0      # denotes removing scaler
        $scope.$digest()

        $scope.save(['name', 'type', 'input_format', 'transformer', 'params', 'required', 'scaler__predefined_selected', 'scaler__name','scaler__type', 'scaler__params', 'default', 'feature_set_id', 'is_target_variable'])
        $httpBackend.flush()
        $scope.$digest()

        expect($scope.savingProgress).toEqual '100%'
        expect($location.url()).toEqual "/models/#{model_id}?action=model:details"
        expect($scope.feature.transformer.type).toEqual 'Dictionary'
        expect($scope.feature.transformer.params).toEqual {'transformer': 'parameters'}

    it 'should handle pretrained in transformer',
      inject (Model, Feature, Transformer, Scaler, Parameters, $filter)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        [configuration, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        updatedFeature = new Feature
          id: feature_id
          feature_set_id: set_id
          name: 'feature'
          type: 'boolean'
          params: {}
          transformer: new Transformer({type: 'Zinger', id: 10})
          scaler: new Scaler({})

        $httpBackend.expectPUT "#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/"
        , (data)->
          featureData = data.getData()
          params = JSON.parse featureData['params']
          valid = true
          valid = valid and featureData['name'] is 'feature'
          valid = valid and featureData['type'] is 'boolean'
          valid = valid and featureData['feature_set_id'] is 222
          valid = valid and featureData['is_target_variable'] is false
          valid = valid and featureData['params'] is $filter('json')({})

          valid = valid and featureData['remove_transformer'] is false
          valid = valid and featureData['transformer-predefined_selected'] is true
          valid = valid and 'transformer-params' not in _.keys(featureData)
          valid = valid and 'transformer-type' not in _.keys(featureData)
          valid = valid and featureData['transformer-transformer'] is 10

          valid = valid and featureData['remove_scaler'] is true
          valid = valid and 'scaler' not in _.keys(featureData)

          if not valid
            console.log 'the post form was not as expected', data.getData()
          return valid
        .respond 200, angular.toJson({feature: updatedFeature})

        $scope.feature.type = 'boolean'
        $scope.feature.transformer.id = 10 # denotes pretrained transformer
        $scope.feature.transformer.type = 'Zinger'
        $scope.feature.scaler.id = 0      # denotes removing scaler
        $scope.$digest()

        $scope.save(['name', 'type', 'input_format', 'transformer', 'params', 'required', 'scaler__predefined_selected', 'scaler__name','scaler__type', 'scaler__params', 'default', 'feature_set_id', 'is_target_variable'])
        $httpBackend.flush()
        $scope.$digest()

        expect($scope.savingProgress).toEqual '100%'
        expect($location.url()).toEqual "/models/#{model_id}?action=model:details"
        expect($scope.feature.transformer.type).toEqual 'Zinger'
        expect($scope.feature.transformer.id).toEqual 10

