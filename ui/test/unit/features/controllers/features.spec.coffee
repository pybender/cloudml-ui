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
        type: 'dict'
      featureLoadResponse = {}
      featureLoadResponse[feature.API_FIELDNAME] = feature
      $httpBackend.expectGET("#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/?show=#{Feature.MAIN_FIELDS}")
      .respond 200, angular.toJson featureLoadResponse

      parameters = new Parameters
      parametersUrl = "#{parameters.BASE_API_URL}/"
      paramsConfig = JSON.parse(map_url_to_response(parametersUrl, 'load parameters configuration')[1]).configuration.params
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
      return [paramsConfig, feature]

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
        [paramsConfig, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        expect($scope.modelObj).toEqual jasmine.any(Model)
        expect($scope.modelObj.id).toEqual model_id

        expect($scope.feature).toEqual jasmine.any(Feature)
        expect($scope.feature.id).toEqual feature_id
        expect($scope.feature.feature_set_id).toEqual set_id
        expect($scope.feature.transformer).toEqual jasmine.any(Transformer)
        expect($scope.feature.scaler).toEqual jasmine.any(Scaler)

        expect($scope.config).toEqual {required_params: [], optional_params: []}
        expect($scope.paramsConfig).toEqual paramsConfig
        expect($scope.requiredParams).toEqual []
        expect($scope.optionalParams).toEqual []
        expect($scope.feature.paramsDict).toEqual {}

        typeTestedCount = 0
        # change type trigger loading feature parameters
        for newType in ['text', 'float', 'numeric', 'int', 'boolean']
          $scope.feature.type = newType
          $scope.$digest()
          expect($scope.requiredParams).toEqual []
          expect($scope.optionalParams).toEqual []
          expect($scope.feature.paramsDict).toEqual {}
          typeTestedCount += 1

        # special case features
        for newType in ['date', 'regex']
          $scope.feature.type = newType
          $scope.$digest()
          expect($scope.requiredParams).toEqual [ 'pattern' ]
          expect($scope.optionalParams).toEqual []
          expect($scope.feature.paramsDict).toEqual { pattern : '' }
          typeTestedCount += 1

        for newType in ['categorical_label', 'categorical']
          $scope.feature.type = 'categorical'
          $scope.$digest()
          expect($scope.requiredParams).toEqual []
          expect($scope.optionalParams).toEqual [ 'split_pattern', 'min_df' ]
          expect($scope.feature.paramsDict).toEqual { split_pattern : '', min_df : '' }
          typeTestedCount += 1

        $scope.feature.type = 'composite'
        $scope.$digest()
        expect($scope.requiredParams).toEqual  [ 'chain' ]
        expect($scope.optionalParams).toEqual []
        expect($scope.feature.paramsDict).toEqual { chain : '' }
        typeTestedCount += 1

        $scope.feature.type = 'map'
        $scope.$digest()
        expect($scope.requiredParams).toEqual  [ 'mappings' ]
        expect($scope.optionalParams).toEqual []
        expect($scope.feature.paramsDict).toEqual { mappings : {  } }
        typeTestedCount += 1

        # As of 20140902: We have 11, and we should have tested them all
        expect(typeTestedCount).toBe 11

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

    it 'save feature',
      inject (Model, Feature, Transformer, Scaler, Parameters)->
        [model_id, set_id, feature_id] = [111, 222, 333]
        [paramsConfig, feature] = prepareTestContext Model, Feature, Transformer,
          Scaler, Parameters, model_id, set_id, feature_id

        $httpBackend.expectPUT("#{Feature.$get_api_url(feature_set_id: set_id)}#{feature_id}/")
        .respond 200, angular.toJson({feature: feature})
        $scope.save(['name', 'type', 'input_format', 'transformer__name', 'transformer__type',  'transformer__params', 'params', 'required', 'scaler__predefined_selected', 'scaler__name','scaler__type', 'scaler__params', 'default', 'feature_set_id', 'is_target_variable'])
        $httpBackend.flush()
        $scope.$digest()
        expect($scope.savingProgress).toEqual '100%'
        expect($location.url()).toEqual "/models/#{model_id}?action=model:details"


