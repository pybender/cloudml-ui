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


  describe 'FeatureEditCtrl', ->

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


    it 'clearing transformer & scaler',
      inject (Model, Feature, Transformer, Scaler, Parameters)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        prepareTestContext Model, Feature, Transformer, Scaler,
          Parameters, model_id, set_id, feature_id

        $scope.feature.transformer = new Transformer
        $scope.clearTransformer()
        expect($scope.feature.transformer).toEqual {}

        $scope.feature.transformer = new Transformer
        $scope.changeTransformerType()
        expect($scope.feature.transformer).toEqual {}

        $scope.feature.scaler = new Scaler
        $scope.clearScaler()
        expect($scope.feature.scaler).toEqual {}

        $scope.feature.transformer = new Transformer
        $scope.changeScalerType()
        expect($scope.feature.scaler).toEqual {}

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

    it 'save feature',
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

        $httpBackend.expectPUT "#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/"
        , (data)->
          featureData = data.getData()
          params = JSON.parse featureData['params']
          valid = featureData['name'] is 'feature' and
            featureData['type'] is 'categorical_label' and
            featureData['feature_set_id'] is 222 and
            featureData['is_target_variable'] is false and
            featureData['remove_transformer'] is true and
            featureData['remove_scaler'] is true and
            params['min_df'] is paramsDict.min_df and
            params['split_pattern'] is paramsDict.split_pattern
          if not valid
            console.log 'the post form was not as expected', data.getData()
          return valid
        .respond 200, angular.toJson({feature: updatedFeature})

        $scope.feature.type = 'categorical_label'
        $scope.feature.paramsDict = paramsDict
        $scope.$digest()

        $scope.save(['name', 'type', 'input_format', 'transformer__name', 'transformer__type',  'transformer__params', 'params', 'required', 'scaler__predefined_selected', 'scaler__name','scaler__type', 'scaler__params', 'default', 'feature_set_id', 'is_target_variable'])
        $httpBackend.flush()
        $scope.$digest()

        expect($scope.savingProgress).toEqual '100%'
        expect($location.url()).toEqual "/models/#{model_id}?action=model:details"
        expect($scope.feature.type).toEqual 'categorical_label'
        expect($scope.feature.paramsDict).toEqual paramsDict
        expect($scope.feature.params).toEqual angular.toJson(paramsDict)


