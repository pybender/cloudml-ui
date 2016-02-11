describe 'features/controllers/named_types.coffee', ->

  beforeEach ->
    module 'ngCookies'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.features.models'
    module 'app.features.controllers.named_types'

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


  describe 'NamedFeatureTypesSelectsLoader', ->

    it 'should init scope ',
      inject (NamedFeatureType)->
        namedTypes = [
          new NamedFeatureType {id:111, name: 'type 111', type: 'boolean'}
        ,
          new NamedFeatureType {id:222, name: 'type 222', type: 'text'}
        ]
        response = {}
        response[namedTypes[0].API_FIELDNAME + 's'] = namedTypes

        $httpBackend.expectGET("#{namedTypes[0].BASE_API_URL}?show=name")
        .respond 200, angular.toJson response
        createController 'NamedFeatureTypesSelectsLoader', {NamedFeatureType: NamedFeatureType}
        $httpBackend.flush()

        expect($scope.types).toEqual NamedFeatureType.$TYPES_LIST.concat ['type 111', 'type 222']

        # handles error
        $scope.setError = jasmine.createSpy('$scope.setError').and.returnValue 'an Error'
        $httpBackend.expectGET("#{namedTypes[0].BASE_API_URL}?show=name")
        .respond 400
        createController 'NamedFeatureTypesSelectsLoader', {NamedFeatureType: NamedFeatureType}
        $httpBackend.flush()

        expect($scope.setError).toHaveBeenCalled()
        expect($scope.err).toEqual 'an Error'


  describe 'FeatureTypeEditCtrl', ->

    prepareTestContext = (Parameters, NamedFeatureType, causeError=false)->
      parameters = new Parameters
      parametersUrl = "#{parameters.BASE_API_URL}/"
      paramsConfig = JSON.parse(map_url_to_response(parametersUrl, 'load parameters configuration')[1]).configuration.params
      if not causeError
        $httpBackend.expectGET("#{parameters.BASE_API_URL}/")
        .respond.apply @, map_url_to_response(parametersUrl, 'load parameters configuration')
      else
        $httpBackend.expectGET("#{parameters.BASE_API_URL}/")
        .respond 400

      createController 'FeatureTypeEditCtrl', {Parameters: Parameters}
      $httpBackend.flush()

      return paramsConfig

    it 'should handle error getting configuration',
      inject (Parameters, NamedFeatureType)->

        $scope.setError = jasmine.createSpy '$scope.setError'
        $scope.model = new NamedFeatureType() # this comes from openDialog openOptions
        $scope.model.type = 'zinger'
        prepareTestContext Parameters, NamedFeatureType, true
        expect($scope.setError).toHaveBeenCalled()

    it 'should init scope properly with everything',
      inject (Parameters, NamedFeatureType)->
        $scope.model = new NamedFeatureType() # this comes from openDialog openOptions
        $scope.model.type = 'zinger'
        paramsConfig = prepareTestContext Parameters, NamedFeatureType

        expect($scope.config).toEqual { required_params : [  ], optional_params : [  ] }
        expect($scope.paramsConfig).toEqual paramsConfig
        expect($scope.requiredParams).toEqual []
        expect($scope.optionalParams).toEqual []

        typeTestedCount = 0
        # change type trigger loading feature parameters
        for newType in ['text', 'float', 'numeric', 'int', 'boolean']
          $scope.model.type = newType
          $scope.$digest()
          expect($scope.requiredParams).toEqual []
          expect($scope.optionalParams).toEqual []
          expect($scope.model.paramsDict).toEqual {}
          typeTestedCount += 1

        # special case features
        for newType in ['date', 'regex']
          $scope.model.type = newType
          $scope.$digest()
          expect($scope.requiredParams).toEqual [ 'pattern' ]
          expect($scope.optionalParams).toEqual []
          expect($scope.model.paramsDict).toEqual { pattern : '' }
          typeTestedCount += 1

        for newType in ['categorical_label', 'categorical']
          $scope.model.type = 'categorical'
          $scope.$digest()
          expect($scope.requiredParams).toEqual []
          expect($scope.optionalParams).toEqual [ 'split_pattern', 'min_df' ]
          expect($scope.model.paramsDict).toEqual { split_pattern : '', min_df : '' }
          typeTestedCount += 1

        $scope.model.type = 'composite'
        $scope.$digest()
        expect($scope.requiredParams).toEqual  [ 'chain' ]
        expect($scope.optionalParams).toEqual []
        expect($scope.model.paramsDict).toEqual { chain : '' }
        typeTestedCount += 1

        $scope.model.type = 'map'
        $scope.$digest()
        expect($scope.requiredParams).toEqual  [ 'mappings' ]
        expect($scope.optionalParams).toEqual []
        expect($scope.model.paramsDict).toEqual { mappings : {  } }
        typeTestedCount += 1

        # As of 20140902: We have 11, and we should have tested them all
        expect(typeTestedCount).toBe 11


  describe 'FeatureTypeListCtrl', ->

    beforeEach ->
      $rootScope.openDialog = (->)
      spyOn($rootScope, 'openDialog').and.returnValue {result: 'then': (->)}

    it 'should init scope and call onto openDialog ',
      inject (NamedFeatureType)->
        createController 'FeatureTypeListCtrl', {NamedFeatureType: NamedFeatureType}

        expect($scope.MODEL).toEqual NamedFeatureType
        expect($scope.FIELDS).toEqual NamedFeatureType.MAIN_FIELDS
        expect($scope.ACTION).toEqual 'loading named feature types'
        expect($scope.LIST_MODEL_NAME).toEqual NamedFeatureType.LIST_MODEL_NAME
        expect($scope.filter_opts).toEqual {'is_predefined': 1}

        # add dialog
        $scope.add()
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: jasmine.any(NamedFeatureType)
          template: 'partials/features/named_types/add.html'
          ctrlName: 'ModelEditDialogCtrl'
          action: 'add new named feature type'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        # edit dialog
        namedType = new NamedFeatureType {id: 999, name: 'type 999'}
        $scope.edit(namedType)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: namedType
          template: 'partials/features/named_types/edit.html'
          ctrlName: 'ModelEditDialogCtrl'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

        # delete dialog
        namedType = new NamedFeatureType {id: 777, name: 'type 777'}
        $scope.delete(namedType)
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: namedType
          template: 'partials/base/delete_dialog.html'
          ctrlName: 'DialogCtrl'
          action: 'delete named feature type'
          path: namedType.BASE_UI_URL
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope
