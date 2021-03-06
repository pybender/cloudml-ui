describe 'ML Models Controllers', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.models.controllers'
    module 'app.models.model'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.datasets.model'
    module 'app.features.models'
    module 'app.testresults.model'

  $httpBackend = null
  $scope = null
  settings = null
  $window = null
  createController = null
  $location = null
  $timeout = null
  $rootScope = null
  $routeParams = null

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $controller = $injector.get('$controller')
    $window = $injector.get('$window')
    $location = $injector.get('$location')
    $timeout = $injector.get('$timeout')
    $routeParams = $injector.get('$routeParams')
    $rootScope = $injector.get('$rootScope')

    $scope = $rootScope.$new()
    spyOn($location, 'path')

    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()

  describe 'ModelListCtrl', ->

    beforeEach inject (Model)->
      $location.search {tag: 'zozo'}
      createController 'ModelListCtrl', {Model: Model, $location: $location}
      expect($scope.MODEL).toEqual Model
      expect($scope.FIELDS).toEqual = ['name','status','locked','servers','tags','created_on',
                                       'created_by', 'updated_on','updated_by', 'comparable'].join(',')
      expect($scope.ACTION).toEqual 'loading models'
      expect($scope.currentTag).toEqual = 'zozo'
      expect($scope.STATUSES).toEqual ['', 'New', 'Queued', 'Importing',
                       'Imported', 'Requesting Instance', 'Instance Started',
                       'Training', 'Trained', 'Error', 'Canceled']

    it  'should init scope, updatedByMe case', ->
      $scope.$digest()

      $scope.$emit = jasmine.createSpy '$scope.$emit'
      $scope.user =
        id: 1111
        name: 'user'

      $scope.init true, 'some_model_name', 'updated_on', 'desc'
      $scope.$digest()

      expect($scope.modelName).toEqual 'some_model_name'
      expect($scope.kwargs).toEqual
        tag: $scope.currentTag
        per_page: 5
        sort_by: 'updated_on'
        order: 'desc'
        page: 1
      expect($scope.filter_opts).toEqual
        updated_by_id: $scope.user.id
        status: ''

      #change filter options
      $scope.filter_opts = {}
      $scope.$digest()
      expect($scope.$emit.calls.mostRecent().args).toEqual ['BaseListCtrl:start:load', 'some_model_name']

    it  'should init scope, no updatedByMe', ->
      $scope.user =
        id: 1111
        name: 'user'

      $scope.init null, 'some_model_name', 'updated_on', 'asc'
      $scope.$digest()

      expect($scope.modelName).toEqual 'some_model_name'
      expect($scope.filter_opts).toEqual
        status: ''

  describe 'AddModelCtl', ->

    it  'should init scope', inject (Model)->
      createController 'AddModelCtl', Model
      expect($scope.model).not.toBeUndefined()

  describe "ModelDetailsCtrl1", ->
    MODEL_ID = '5566'
    BASE_URL = null

    beforeEach ->
      url = settings.apiUrl + 'tags/?show=' + 'text,id'
      BASE_URL = settings.apiUrl + 'models/'
      $httpBackend.expectGET(url).respond('{"tags": [{"text": "smth"}]}')
      $routeParams.id = MODEL_ID
      $scope.initSections = jasmine.createSpy()

      createController "ModelDetailsCtrl"
      $httpBackend.flush()

      expect($scope.model.id).toEqual(MODEL_ID)
      expect($scope.LOADED_SECTIONS).toBeDefined()
      expect($scope.select2params).toBeDefined()
      expect($scope.params).toBeDefined()

    it "should make details request", inject (MODEL_FIELDS, FIELDS_BY_SECTION) ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + MODEL_FIELDS + ',' + FIELDS_BY_SECTION['model']
      $httpBackend.expectGET(url).respond.apply @, map_url_to_response(url, 'multiclass model main fields')
      $scope.model.status = 'Trained'

      s3_url = "#{BASE_URL}#{$scope.model.id}/action/trainer_download_s3url/"
      $httpBackend.expectGET(s3_url)
      .respond "{\"trainer_file_for\": #{MODEL_ID}, \"url\": \"https://.s3.amazonaws.com/9c4012780c0111e4968b000c29e3f35c?Signature=%2FO7%2BaUv4Fk84ioxWigRwkcdgVM0\"}"
      $scope.goSection(['model'])
      $httpBackend.flush()
      expect($scope.model.trainer_s3_url).toEqual 'https://.s3.amazonaws.com/9c4012780c0111e4968b000c29e3f35c?Signature=%2FO7%2BaUv4Fk84ioxWigRwkcdgVM0'

    it "should request only features", inject (FIELDS_BY_SECTION) ->
      url = BASE_URL + MODEL_ID + '/' + '?show=' + FIELDS_BY_SECTION['main']
      $httpBackend.expectGET(url).respond('{"model": [{"id": "' + MODEL_ID + '"}]}')

      $scope.goSection(['features'])
      $httpBackend.flush()


  describe 'ModelDetailsCtrl', ->

    prepareContext = null
    beforeEach inject (Model, TestResult, Tag, FIELDS_BY_SECTION, $q)->
      prepareContext = (errorTagLoding=false)->
        $rootScope.setError = jasmine.createSpy '$rootScope.setError'
        $scope = $rootScope.$new()
        $scope.$broadcast = jasmine.createSpy '$scope.$broadcast'

        # prepare tags request
        tag = new Tag
        response = {}
        response[tag.API_FIELDNAME + 's'] = [
          new Tag
            id: 999
            text: 'tag999'
        , new Tag
            id: 888
            text: 'tag888'
        ]

        if not errorTagLoding
          $httpBackend.expectGET "#{tag.BASE_API_URL}?show=text,id"
          .respond 200, angular.toJson(response)
        else
          $httpBackend.expectGET "#{tag.BASE_API_URL}?show=text,id"
          .respond 400

        $routeParams = {id: 111}
        $scope.initSections = jasmine.createSpy '$scope.initSections'
        createController 'ModelDetailsCtrl',
          $location: $location
          $routeParams: {id: 111}
          Model: Model
          TestResult: TestResult
          Tag: Tag
          FIELDS_BY_SECTION: FIELDS_BY_SECTION
          $q: $q
        $httpBackend.flush()

        expect($scope.model.id).toEqual = $routeParams.id
        expect($scope.LOADED_SECTIONS).toEqual []
        expect($scope.params).toEqual {'tags': []}
        if not errorTagLoding
          expect(({id: t.id, text: t.text} for t in $scope.tag_list)).toEqual [
            id: 999
            text: 'tag999'
          ,
            id: 888
            text: 'tag888'
          ]
        else
          expect($scope.tag_list).toBeUndefined()

    it  'should throw exception if no routeParams.id',
      inject (Model, TestResult, Tag, FIELDS_BY_SECTION, $q)->
        expect ->
          createController 'ModelDetailsCtrl',
            $location: $location
            $routeParams: {}
            Model: Model
            TestResult: TestResult
            Tag: Tag
            FIELDS_BY_SECTION: FIELDS_BY_SECTION
            $q: $q
        .toThrow new Error 'Can\'t initialize without model id'

    it  'should have select2params properly working', inject ($compile)->
      prepareContext()

      expect($scope.select2params.multiple).toEqual true
      expect($scope.select2params.query({callback: (d)-> d})).toEqual {results:
        [{text: 'tag999', id : 999}, {text : 'tag888', id : 888}]}
      elem = $compile('<div></div>')($scope)
      elem[0].text = 'something'
      expect($scope.select2params.createSearchChoice 'zinger', elem)
      .toEqual {id: 'zinger', text: 'zinger'}

      elem[0].text = 'zinger'
      expect($scope.select2params.createSearchChoice 'zinger', elem)
      .toBeUndefined()

      # trigger a watch
      expect($scope.params.tags).toEqual []
      $scope.params.tags = '999'
      $scope.$digest()
      expect($scope.params.tags).toEqual [{id: 999, text: 'tag999'}]

      $scope.params.tags = 'new_tag,999'
      $scope.$digest()
      expect($scope.params.tags).toEqual [{id: 'new_tag', text: 'new_tag'},
        {id: 999, text: 'tag999'}]

      $scope.params.tags = 'new_tag,999,888'
      $scope.$digest()
      expect($scope.params.tags).toEqual [{id: 'new_tag', text: 'new_tag'},
        {id: 999, text: 'tag999'}, {id: 888, text: 'tag888'}]

    it  'should handle errors loading tags', inject (Model, MODEL_FIELDS)->
      prepareContext(true)
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'loading tags'

    it  'should handle no fields case', inject (Model, MODEL_FIELDS)->
      prepareContext()

      $scope.load('', '')
      expect($scope.LOADED_SECTIONS).toEqual []

    it  'should load main and test section with tags and caching', inject (Model, MODEL_FIELDS, FIELDS_BY_SECTION, $timeout)->
      prepareContext()

      expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

      model = new Model
        id: $scope.model.id
      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=#{MODEL_FIELDS},#{FIELDS_BY_SECTION['model']}"
      .respond 200, angular.toJson(response)

      $scope.model.tags = ['tag1', 'tag2']
      $scope.goSection ['model', 'details']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['model', 'main']
      expect($scope.$broadcast).not.toHaveBeenCalledWith()
      expect($scope.params.tags).toEqual [{id: 'tag1', text: 'tag1'}, {id: 'tag2', text: 'tag2'}]

      $scope.goSection ['test', '']
      $scope.$digest()
      $timeout.flush()
      expect($scope.LOADED_SECTIONS).toEqual ['model', 'main', 'test']
      expect($scope.$broadcast).toHaveBeenCalledWith 'loadTest', true

      # cached should not reload tests
      $scope.$broadcast.calls.reset()
      $scope.goSection ['test', '']
      $scope.$digest()
      expect($scope.LOADED_SECTIONS).toEqual ['model', 'main', 'test']
      expect($scope.$broadcast).not.toHaveBeenCalledWith()

    it  'should load features and caching', inject (Model, MODEL_FIELDS, FIELDS_BY_SECTION)->
      prepareContext()

      expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

      model = new Model
        id: $scope.model.id
      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=features"
      .respond 200, angular.toJson(response)
      $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=#{MODEL_FIELDS},#{FIELDS_BY_SECTION['model']}"
      .respond 200, angular.toJson(response)

      $scope.goSection ['model', 'json']
      $httpBackend.flush()

      expect($scope.LOADED_SECTIONS).toEqual ['model', 'main']

      # no caching in model:json section
      $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=features"
      .respond 200, angular.toJson(response)
      $scope.goSection ['model', 'json']
      $httpBackend.flush()
      expect($scope.LOADED_SECTIONS).toEqual ['model', 'main']

    it  'should load main for trained model and update its tags, and handles errors saving tags',
      inject (Model, MODEL_FIELDS, FIELDS_BY_SECTION, Tag)->

        prepareContext()

        expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

        model = new Model
          id: $scope.model.id
          status: 'Trained'
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=#{MODEL_FIELDS},#{FIELDS_BY_SECTION['training']}"
        .respond 200, angular.toJson(response)
        response =
          url: 'http://something.com/path/to/some/file.dat'
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/action/trainer_download_s3url/"
        .respond 200, angular.toJson(response)

        $scope.goSection ['training', '']
        $httpBackend.flush()

        expect($scope.LOADED_SECTIONS).toEqual ['training', 'main']
        expect($scope.model.trainer_s3_url).toEqual 'http://something.com/path/to/some/file.dat'

        # caching
        $scope.goSection ['training', '']
        expect($scope.LOADED_SECTIONS).toEqual ['training', 'main']

        $scope.params.tags = [
          new Tag
            id: 111
            text: 'tag111'
        ,
          new Tag
            id: 222
            text: 'tag222'
        ]
        model = new Model
          id: $scope.model.id
          status: 'Trained'
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectPUT "#{model.BASE_API_URL}#{$scope.model.id}/"
        .respond 200, angular.toJson(response)
        $scope.updateTags()
        $httpBackend.flush()

        expect($scope.model.tags).toEqual ['tag111', 'tag222']

        # saving tags error
        $rootScope.setError.calls.reset()
        $httpBackend.expectPUT "#{model.BASE_API_URL}#{$scope.model.id}/"
        .respond 400
        $scope.updateTags()
        $httpBackend.flush()

        expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'saving model tags'

        # clearing tags
        $scope.params.tags = []
        response[model.API_FIELDNAME] = model
        $httpBackend.expectPUT "#{model.BASE_API_URL}#{$scope.model.id}/"
        .respond 200, angular.toJson(response)
        $scope.updateTags()
        $httpBackend.flush()

        expect($scope.model.tags).toEqual []

    it  'should handle load error',
      inject (Model, MODEL_FIELDS, FIELDS_BY_SECTION)->
        prepareContext()

        expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

        model = new Model
          id: $scope.model.id
          status: 'Trained'
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=#{MODEL_FIELDS},#{FIELDS_BY_SECTION['training']}"
        .respond 400

        $scope.goSection ['training', '']
        $httpBackend.flush()

        expect($scope.LOADED_SECTIONS).toEqual []
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading model details'

    it  'should handle getting s3 url of model error',
      inject (Model, MODEL_FIELDS, FIELDS_BY_SECTION)->
        prepareContext()
        
        expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

        model = new Model
          id: $scope.model.id
          status: 'Trained'
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=#{MODEL_FIELDS},#{FIELDS_BY_SECTION['training']}"
        .respond 200, angular.toJson(response)
        response =
          url: 'http://something.com/path/to/some/file.dat'
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/action/trainer_download_s3url/"
        .respond 400

        $scope.goSection ['training', '']
        $httpBackend.flush()

        expect($scope.LOADED_SECTIONS).toEqual ['training', 'main']
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading trainer s3 url'

    it 'should watch for training progress and update model status until it is done',
      inject (Model)->
        prepareContext()

        expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

        model = new Model
          id: $scope.model.id
          status: 'Trained'
          training_in_progress: false
          error: ''
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=status,training_in_progress,error,segments"
        .respond 200, angular.toJson(response)

        $scope.model.training_in_progress = true
        $scope.model.status = 'Training'
        $scope.$digest()
        $timeout.flush()
        $httpBackend.flush()
        expect($scope.model.status).toEqual 'Trained'
        expect($scope.model.training_in_progress).toBe false

        $timeout.cancel = jasmine.createSpy '$timeout.cancel'
        $scope.$emit '$destroy'
        expect($timeout.cancel).toHaveBeenCalled

    it 'should watch for predefined classifier changes and update it on page',
      inject (Model, Classifier)->
        prepareContext()

        expect($scope.initSections).toHaveBeenCalledWith $scope.goSection

        model = new Model
          id: $scope.model.id
          classifier:
            type: 'random forest classifier'
        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{$scope.model.id}/?show=classifier"
        .respond 200, angular.toJson(response)

        $scope.model.classifier = new Classifier
          type: 'desicion tree classifier'
          name: ''

        $scope.model.classifier.name = 'My predefined'
        $scope.model.classifier.predefined_selected = true
        $scope.$digest()
        $httpBackend.flush()
        expect($scope.model.classifier.type).toEqual 'random forest classifier'
        expect($scope.model.classifier.name).toEqual 'My predefined'


  describe 'BaseModelDataSetActionCtrl', ->

    it  'init scope multiple dataset', ->
      $rootScope.data = {}
      $rootScope.handler = {id: 11, name: 'some_handler', import_params: 'someimportparams'}
      $rootScope.multiple_dataset = true
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'
      createController 'BaseModelDataSetActionCtrl', {$rootScope: $rootScope}

      expect($scope.data.format).toEqual 'json'
      expect($scope.data.new_dataset_selected).toBe 0
      expect($scope.data.existing_instance_selected).toBe 1
      expect($scope.formats).toEqual [{name: 'JSON', value: 'json'},
        {name: 'CSV', value: 'csv'}]
      expect($scope.select2Options).toEqual
        allowClear: true
        placeholder: jasmine.any(String)
        width: jasmine.any(Number)
      expect($scope.params).toEqual $rootScope.handler.import_params

      $scope.close()
      expect($rootScope.resetError).toHaveBeenCalled()
      expect($rootScope.$close).toHaveBeenCalled()

    it  'init scope single dataset', ->
      $rootScope.data = {}
      $rootScope.handler = {id: 11, name: 'some_handler', import_params: 'someimportparams'}
      $rootScope.multiple_dataset = false
      createController 'BaseModelDataSetActionCtrl', {$rootScope: $rootScope}

      expect($scope.data.format).toEqual 'json'
      expect($scope.data.new_dataset_selected).toBe 0
      expect($scope.data.existing_instance_selected).toBe 1
      expect($scope.formats).toEqual [{name: 'JSON', value: 'json'},
        {name: 'CSV', value: 'csv'}]
      expect($scope.select2Options).toEqual
        allowClear: true
      expect($scope.params).toEqual $rootScope.handler.import_params


  describe 'TrainModelCtrl', ->

    it  'init scope', inject (Model)->

      model = new Model
        id: 999
        name: 'someModel'
        train_import_handler_obj: {id: 888, name: 'some_handler_for_training'}
      openOptions = {model: model}
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

      createController 'TrainModelCtrl', {$rootScope: $rootScope, openOptions: openOptions}

      expect($rootScope.resetError).toHaveBeenCalled()
      expect($scope.model).toEqual openOptions.model
      expect($scope.data).toEqual {}
      expect($scope.handler).toEqual openOptions.model.train_import_handler_obj
      expect($scope.multiple_dataset).toBe true

      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/train/"
      .respond 200, angular.toJson(response)
      $scope.start()
      $httpBackend.flush()
      expect($rootScope.$close).toHaveBeenCalled()

      # error saving the model
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/train/"
      .respond 400
      $scope.start()
      $httpBackend.flush()
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'starting someModel training'


  describe 'ModelActionsCtrl', ->

    beforeEach ->
      $rootScope.openDialog = (->)
      spyOn($rootScope, 'openDialog').and.returnValue {result: 'then': (->)}
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      createController 'ModelActionsCtrl'
      expect($scope.init).toBeDefined()
      expect($scope.test_model).toBeDefined()
      expect($scope.cancel_request_spot_instance).toBeDefined()
      expect($scope.train_model).toBeDefined()
      expect($scope.delete_model).toBeDefined()
      expect($scope.editClassifier).toBeDefined()
      expect($scope.uploadModelToPredict).toBeDefined()
      expect($scope._showModelActionDialog).toBeDefined()
      expect($scope._showModelActionDialog).toBeDefined()


    it  'should throw error when initialized with no model', ->
      expect($scope.init).toThrow new Error 'Please specify model'
      expect(-> $scope.init({})).toThrow new Error 'Please specify model'
      expect(-> $scope.init({model: null})).toThrow new Error 'Please specify model'

    it  'should work with a model and open testing dialog', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      $scope.init {model: model}
      expect($scope.model).toEqual model

      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=test_import_handler"
      .respond 200, angular.toJson response
      $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=test_handler_fields"
      .respond 200, angular.toJson response
      $scope.test_model model
      $httpBackend.flush()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: model
        template: 'partials/testresults/run_test.html'
        ctrlName: 'TestDialogController'
        cssClass: 'modal large'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it  'should work with a model and open testing dialog but with calling model.test_import_handler_obj',
      inject (Model, XmlImportHandler)->
        model = new Model
          id: 999
          name: 'model-name'
          test_import_handler_obj: 'bogus'

        $scope.init {model: model}
        expect($scope.model).toEqual model

        response = {}
        response[model.API_FIELDNAME] = model
        $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=test_handler_fields"
        .respond 200, angular.toJson response

        $scope.test_model model
        $httpBackend.flush()

        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: model
          template: 'partials/testresults/run_test.html'
          ctrlName: 'TestDialogController'
          cssClass: 'modal large'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it  'should cancel request spot instance', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/cancel_request_instance/"
      .respond 200, angular.toJson response
      $scope.cancel_request_spot_instance model
      $httpBackend.flush()

    it  'should open train model dialog', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      response = {}
      response[model.API_FIELDNAME] = model
      $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=train_import_handler"
      .respond 200, angular.toJson response
      $scope.train_model model
      $httpBackend.flush()

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: model
        template: 'partials/models/model_train_popup.html'
        ctrlName: 'TrainModelCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it  'should handle errors retrieving train_import_handler', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=train_import_handler"
      .respond 400
      $scope.train_model model
      $httpBackend.flush()
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'loading import handler details'

    it  'should open delete model dialog', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      $scope.delete_model model

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: model
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DialogCtrl'
        action: 'delete model'
        path: model.BASE_UI_URL
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it  'should open edit classifier dialog', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      $scope.editClassifier model

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: null
        template: 'partials/features/classifiers/edit.html'
        ctrlName: 'ModelWithParamsEditDialogCtrl'
        action: 'edit classifier'
        extra: {model: model, fieldname: 'classifier'}
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it  'should open upload to predict', inject (Model)->
      model = new Model
        id: 999
        name: 'model-name'

      $scope.uploadModelToPredict model

      expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
        model: model
        template: 'partials/servers/choose_server_for_model.html'
        ctrlName: 'ModelUploadToServerCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it 'should call to import_ih_fields_to_features and reload on success',
      inject (Model, $route)->
        spyOn $route, 'reload'
        $scope.model = new Model
          id: 111
          name: 'new model'

        $httpBackend.expectPUT "#{$scope.model.BASE_API_URL}#{$scope.model.id}/action/import_features_from_xml_ih/"
        .respond 200, ""

        $scope.import_ih_fields_to_features()

        $httpBackend.flush()

        expect($route.reload).toHaveBeenCalled()

    it 'should call to import_ih_fields_to_features and handle errors',
      inject (Model, $route)->
        spyOn $route, 'reload'
        $scope.model = new Model
          id: 111
          name: 'new model'

        $httpBackend.expectPUT "#{$scope.model.BASE_API_URL}#{$scope.model.id}/action/import_features_from_xml_ih/"
        .respond 400, ""

        $scope.import_ih_fields_to_features()

        $httpBackend.flush()

        expect($route.reload).not.toHaveBeenCalled()
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'adding training import handler fields as features'


  describe 'ModelFeaturesJsonEditCtrl', ->

    it 'should store the original features json and reset it', ->

      createController 'ModelFeaturesJsonEditCtrl'

      $scope.model = {features: '{"schema": "example", "features": {"feature1": "lala", "feature2": "ololo"}}'}
      $scope.FeaturesJsonForm = {fJson: {$setPristine: jasmine.createSpy '$setPristine'}}
      $scope.$digest()

      expect($scope.model.originalJson).toEqual $scope.model.features

      $scope.model.features = '{"schema": "example1", "features": {"feature1": "alala", "feature2": "ololo"}}'
      $scope.$digest()

      $scope.resetJsonChanges()
      expect($scope.model.originalJson).toEqual '{"schema": "example", "features": {"feature1": "lala", "feature2": "ololo"}}'
      expect($scope.model.features).toEqual $scope.model.originalJson

  describe 'save json', ->
    prepareContext = (Model, withError)->
      createController 'ModelFeaturesJsonEditCtrl'
      $scope.setError = jasmine.createSpy '$scope.setError'

      fJson = '{"schema": "example", "features": {"feature1": "lala", "feature2": "ololo"}}'
      $scope.model = new Model({id: 111, features: fJson})
      $scope.FeaturesJsonForm = {fJson: {$setPristine: jasmine.createSpy '$setPristine'}}
      $scope.$digest()

      url = "#{$scope.model.BASE_API_URL}#{$scope.model.id}/"
      $httpBackend.expectPUT url, (features)->
        return fJson
      .respond (if withError then 400 else 200), angular.toJson($scope.model)

      $scope.saveJson()
      $httpBackend.flush()

    it 'should handle errors when saveJson', inject (Model)->

      prepareContext Model, true
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'saving model features JSON'


    it 'should succeed saveJson', inject (Model, $route)->

      spyOn($route, 'reload')

      prepareContext Model, false
      expect($scope.setError).not.toHaveBeenCalled()
      expect($route.reload).toHaveBeenCalled()


  describe 'ModelUploadToServerCtrl', ->

    it  'should init scope', inject (Model)->
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'

      model = new Model
        id: 888
        name: 'zozo888'
      openOptions = {model: model}
      createController 'ModelUploadToServerCtrl', {$rootScope: $rootScope, openOptions: openOptions}

      expect($rootScope.resetError).toHaveBeenCalled()
      expect($scope.model).toEqual model
      expect($scope.model.server).toBe null

      response = {status: 'AOK Fellow'}
      response[model.API_FIELDNAME] = model
      response['status']
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/action/upload_to_server/"
      .respond 200, angular.toJson response
      $scope.upload()
      $httpBackend.flush()

      expect($rootScope.$close).toHaveBeenCalled()
      expect($rootScope.msg).toEqual 'AOK Fellow'

  describe 'ModelDataSetDownloadCtrl', ->

    it  'should have no downloads', ->
      inject (Model) ->
        createController 'ModelDataSetDownloadCtrl', Model
        expect($rootScope.downloads).toEqual {}

        model = new Model
          id: 999
        downloads = {}
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        $scope.getDataSetsDownloads model.id
        $httpBackend.flush()

        expect($rootScope.downloads).toEqual downloads

    it  "should have two downloads", ->
      inject (Model) ->
        createController 'ModelDataSetDownloadCtrl', Model

        model = new Model
          id: 999
        downloads = [{dataset: {id: 1}, task: {}}, {dataset: {id: 2}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        $scope.getDataSetsDownloads model.id
        $httpBackend.flush()

        expect($rootScope.downloads).toEqual downloads
        expect($rootScope.downloads.length).toEqual 2

    it  "should put new download request", ->
      inject (Model) ->
        model = new Model({id: 888})
        downloads = [{dataset: {id: 1}, task: {}}, {dataset: {id: 2}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'
        $scope.getDataSetsDownloads()
        $httpBackend.flush()

        downloads = [{dataset: {id: 1}, task: {status: 'Completed'}}, {dataset: {id: 2}, task: {}}, {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectPUT(url).respond angular.toJson {dataset: 3}

        $scope.requestDataSetDownload 3
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.downloads.length).toEqual 3
        expect($scope.downloadRequested).toBe true
        expect($rootScope.dl_msg).toContain "DataSet has been queued for transformation/vectorization"

    it  "should put new download request with err", ->
      inject (Model) ->
        model = new Model({id: 888})
        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'

        # handles request error
        $scope.setError = jasmine.createSpy('$scope.setError')

        downloads = [{dataset: {id: 1}, task: {status: 'Completed'}}, {dataset: {id: 2}, task: {}}, {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectPUT(url).respond 400

        $scope.requestDataSetDownload 3
        $timeout.flush()
        $httpBackend.flush()

        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'requesting dataset 3 for download'
        expect($scope.downloadRequested).toBe false
        expect($rootScope.dl_msg).toContain "Checking in-progress requests"

    it  "should handle error on get downloads for new download request", ->
      inject (Model) ->
        model = new Model({id: 888})
        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'

        # handles request error
        $scope.setError = jasmine.createSpy('$scope.setError')

        downloads = [{dataset: {id: 1}, task: {status: 'Completed'}}, {dataset: {id: 2}, task: {}}, {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond 500

        $scope.requestDataSetDownload 3
        $timeout.flush()
        $httpBackend.flush()

        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading dataset downloads request'
        expect($scope.downloadRequested).toBe false

    it  "should refuse to put new download request", ->
      inject (Model) ->
        model = new Model({id: 777})
        downloads = [{dataset: {id: 1}, task: {status: 'In Progress'}},
          {dataset: {id: 2}, task: {}},
          {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond 200, angular.toJson
          model: model.id
          downloads: downloads

        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'

        $scope.requestDataSetDownload 3
        $timeout.flush()
        $httpBackend.flush()
        expect($scope.downloadRequested).toBe true
        expect($rootScope.dl_msg).toContain "Please, check in-progress DataSet transformation request"

    it  "should check full scenario of dataset downloads",
      inject (Model) ->
        model = new Model({id: 888})
        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'

        downloads = [{dataset: {id: 1}, task: {status: 'Completed'}}, {dataset: {id: 2}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectPUT(url).respond angular.toJson {dataset: 3}

        $scope.requestDataSetDownload 3
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.downloads.length).toEqual 2
        expect($scope.downloadRequested).toBe true
        expect($rootScope.dl_msg).toContain "DataSet has been queued for transformation/vectorization"

        downloads = [{dataset: {id: 1}, task: {status: 'Completed'}}, {dataset: {id: 2}, task: {}}, {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.downloads.length).toEqual 3
        expect($scope.downloadRequested).toBe true
        expect($rootScope.dl_msg).toContain "DataSet has been queued for transformation/vectorization"


  describe "GridSearchParametersCtrl", ->

    it 'should init scope', inject (Model)->
      model = new Model({
        id: '4321',
        name: 'NN'
        train_import_handler_obj: {id: 888, name: 'some_handler_for_training'}
        classifier: {id: 222, type: 'random forest'}
      })
      openOptions = {model: model}
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $scope.$close = jasmine.createSpy '$scope.$close'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      $rootScope.setSection = jasmine.createSpy '$rootScope.setSection'
      createController "GridSearchParametersCtrl", {$rootScope: $rootScope, openOptions: openOptions}
      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.data).toEqual {parameters: {}}
      expect($scope.handler.id).toEqual 888
      url = "#{settings.apiUrl}features/classifiers/#{model.classifier.id}/action/configuration/"
      resp = {configuration: {'random forest': {"parameters": {"param1": "p1", "param2": "p2"}}}}
      $httpBackend.expectGET(url).respond 200, angular.toJson resp
      $httpBackend.flush()
      expect($scope.params).toEqual {param1: "p1", param2: "p2"}

      url = "#{model.BASE_API_URL}#{model.id}/action/grid_search/"
      resp = {model: model}
      $httpBackend.expectPUT(url).respond 200, angular.toJson resp
      $scope.start {}
      $httpBackend.flush()
      expect($scope.model.grid_search_in_progress).toBe true
      expect($scope.$close).toHaveBeenCalled()
      expect($rootScope.setSection.calls.mostRecent().args[0]).toEqual ['grid_search', 'details']

      # with error
      $httpBackend.expectPUT(url).respond 400, "{}"
      $scope.start {}
      $httpBackend.flush()
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'starting NN searching for classifier parameters'

    it 'should init scope with configuration error', inject (Model)->
      model = new Model({
        id: '4321',
        train_import_handler_obj: {id: 888, name: 'some_handler_for_training'}
        classifier: {id: 222, type: 'random forest'}
      })
      openOptions = {model: model}
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      $scope.setError = jasmine.createSpy '$scope.setError'
      createController "GridSearchParametersCtrl", {$rootScope: $rootScope, openOptions: openOptions}
      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.data).toEqual {parameters: {}}
      expect($scope.handler.id).toEqual 888
      url = "#{settings.apiUrl}features/classifiers/#{model.classifier.id}/action/configuration/"
      $httpBackend.expectGET(url).respond 400, "{}"
      $httpBackend.flush()
      expect($scope.params).toBeUndefined
      expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading types and parameters'

    it 'should init scope with classifier type error', inject (Model)->
      model = new Model({
        id: '4321',
        train_import_handler_obj: {id: 888, name: 'some_handler_for_training'}
        classifier: {id: 222}
      })
      openOptions = {model: model}
      $rootScope.resetError = jasmine.createSpy '$rootScope.resetError'
      createController "GridSearchParametersCtrl", {$rootScope: $rootScope, openOptions: openOptions}
      expect($scope.resetError).toHaveBeenCalled()
      expect($scope.data).toEqual {parameters: {}}
      expect($scope.handler.id).toEqual 888
      expect($scope.inactive).toBe true
      expect($scope.err).toEqual "Need to specify classifier before performing grid search"


  describe "GridSearchResultsCtrl", ->

    beforeEach inject (Model) ->
      $scope.model = new Model({
        id: '4321',
        classifier_grid_params: [{
          id: 3
          status: 'Completed'
        }]
      })
      createController "GridSearchResultsCtrl"

    it "should reload items", inject () ->
      model = $scope.model
      url = "#{model.BASE_API_URL}#{model.id}/?show=classifier_grid_params"
      resp = {"model": $scope.model}
      $httpBackend.expectGET(url).respond 200, angular.toJson resp

      $scope.reload()
      $httpBackend.flush()
      expect($scope.model.grid_search_in_progress).toBe false
      expect($scope.reload_counter).toEqual 0

      # reloading
      $scope.model.classifier_grid_params[0].status = 'Calculating'
      resp = {"model": $scope.model}
      $httpBackend.expectGET(url).respond 200, angular.toJson resp

      $scope.model.classifier_grid_params[0].status = 'Completed'
      resp1 = {"model": $scope.model}
      $httpBackend.expectGET(url).respond 200, angular.toJson resp1

      $scope.reload()
      $httpBackend.flush()
      expect($scope.model.grid_search_in_progress).toBe false
      expect($scope.reload_counter).toEqual 1

    it 'should watch for grid search', inject () ->
      $scope.reload = jasmine.createSpy()
      $scope.model.grid_search_in_progress = true
      $scope.$digest()
      expect($scope.reload).toHaveBeenCalled()


  describe "FeaturesTransformersDataCtrl", ->

    beforeEach inject (Model) ->
      $scope.model = new Model({
        id: '4321'
      })
      createController "FeaturesTransformersDataCtrl"
      $scope.url = "#{$scope.model.BASE_API_URL}#{$scope.model.id}/action/transformers_download/"

    it "should init scope", inject () ->
      expect($scope.tf_segment).toEqual ''
      expect($scope.tf_format).toEqual ''
      expect($scope.formats[0].name).toEqual 'JSON'
      expect($rootScope.tf_dl_msg).toEqual ''
      expect($rootScope.tf_downloads).toEqual {}

    it  'should have no downloads', ->
      inject () ->
        downloads = {}
        $httpBackend.expectGET($scope.url).respond angular.toJson
          model: $scope.model.id
          downloads: downloads

        $scope.getTransformersDownloads $scope.model.id
        $httpBackend.flush()

        expect($rootScope.tf_downloads).toEqual downloads

    it  "should have two downloads", ->
      inject () ->
        downloads = [{segment: {id: 1}, task: {}}, {segment: {id: 2}, task: {}}]
        $httpBackend.expectGET($scope.url).respond angular.toJson
          model: $scope.model.id
          downloads: downloads

        $scope.getTransformersDownloads $scope.model.id
        $httpBackend.flush()

        expect($rootScope.tf_downloads).toEqual downloads
        expect($rootScope.tf_downloads.length).toEqual 2

    it  "should put new download request", ->
      inject () ->
        $httpBackend.expectPUT($scope.url).respond angular.toJson {segment: 'default', data_format: 'json'}
        $scope.requestTransformersDownload 3
        $httpBackend.flush()
        expect($rootScope.tf_dl_msg).toContain "Segment data has been queued "
        downloads = [{segment: {id: 1}, task: {status: 'Completed'}}, {segment: {id: 2}, task: {}}, {segment: {id: 3}, task: {}}]
        $httpBackend.expectGET($scope.url).respond angular.toJson
          model: $scope.model.id
          downloads: downloads
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.tf_downloads.length).toEqual 3

    it  "should put new download request with err", ->
      inject () ->
        # handles request error
        $scope.setError = jasmine.createSpy('$scope.setError')
        $httpBackend.expectPUT($scope.url).respond 400
        $scope.requestTransformersDownload 3
        $httpBackend.flush()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'requesting transformers downloads'

    it  "should handle error on get downloads for new download request", ->
      inject () ->
        # handles request error
        $scope.setError = jasmine.createSpy('$scope.setError')
        $httpBackend.expectPUT($scope.url).respond angular.toJson {segment: 'default', data_format: 'json'}
        $scope.requestTransformersDownload 3
        $httpBackend.flush()
        $httpBackend.expectGET($scope.url).respond 500
        $timeout.flush()
        $httpBackend.flush()
        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'loading transformers downloads'
        expect($scope.downloadRequested).toBe false

    it  "should check full scenario of transformers downloads",
      inject () ->
        $httpBackend.expectPUT($scope.url).respond angular.toJson {segment: 3}
        $scope.requestTransformersDownload 3
        $httpBackend.flush()
        expect($rootScope.tf_dl_msg).toContain "Segment data has been queued"
        downloads = [{segment: {id: 1}, task: {status: 'In Progress'}}, {segment: {id: 2}, task: {}}, {segment: {id: 3}, task: {}}]
        $httpBackend.expectGET($scope.url).respond angular.toJson
          model: $scope.model.id
          downloads: downloads
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.tf_downloads.length).toEqual 3
        downloads = [{segment: {id: 1}, task: {status: 'Completed'}}, {segment: {id: 2}, task: {}}, {segment: {id: 3}, task: {}}]
        $httpBackend.expectGET($scope.url).respond angular.toJson
          model: $scope.model.id
          downloads: downloads
        $timeout.flush()
        $httpBackend.flush()
        expect($rootScope.tf_downloads.length).toEqual 3
        expect($rootScope.tf_dl_msg).toEqual ""

    it  "should set flag for showLogs",
      inject () ->
        expect($scope.open_logs_task_id).toBe null

        $scope.showLogs 3
        expect($scope.open_logs_task_id).toEqual 3

        $scope.showLogs 3
        expect($scope.open_logs_task_id).toBe null
