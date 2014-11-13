describe 'models/controllers.coffee', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.models.controllers'
    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
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

  beforeEach inject ($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $scope = $rootScope.$new()
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


  describe 'TagCtrl', ->

    it  'should init scope with current tag', ->
      $location.search {tag: 'zozo'}
      createController 'TagCtrl'
      expect($scope.currentTag).toEqual 'zozo'


  describe 'ModelListCtrl', ->

    beforeEach inject (Model, MODEL_FIELDS)->
      $location.search {tag: 'zozo'}
      createController 'ModelListCtrl', {Model: Model, $location: $location, MODEL_FIELDS: MODEL_FIELDS}
      expect($scope.MODEL).toEqual Model
      expect($scope.FIELDS).toEqual = MODEL_FIELDS + ',' +
        ['tags','created_on','created_by', 'updated_on','updated_by', 'comparable'].join(',')
      expect($scope.ACTION).toEqual 'loading models'
      expect($scope.currentTag).toEqual = 'zozo'
      expect($scope.kwargs).toEqual
        tag: $scope.currentTag
        per_page: 5
        sort_by: 'updated_on'
        order: 'desc'
      expect($scope.page).toBe 1
      expect($scope.STATUSES).toEqual ['', 'New', 'Queued', 'Importing',
                       'Imported', 'Requesting Instance', 'Instance Started',
                       'Training', 'Trained', 'Error', 'Canceled']

    it  'should init scope, updatedByMe case', ->
      $scope.$digest()

      $scope.$emit = jasmine.createSpy '$scope.$emit'
      $scope.user =
        id: 1111
        name: 'user'

      $scope.init true, 'some_model_name'
      $scope.$digest()

      expect($scope.modelName).toEqual 'some_model_name'
      expect($scope.filter_opts).toEqual
        updated_by_id: $scope.user.id
        status: ''

      #change filter options
      $scope.filter_opts = {}
      $scope.$digest()
      expect($scope.$emit.calls.mostRecent().args).toEqual ['BaseListCtrl:start:load', 'some_model_name']

      # showMore
      $scope.page = 2
      $scope.showMore()
      expect($scope.$emit.calls.mostRecent().args).toEqual ['BaseListCtrl:start:load', 'some_model_name', true, {'page': 3}]

    it  'should init scope, no updatedByMe', ->
      $scope.$digest()

      $scope.$emit = jasmine.createSpy '$scope.$emit'

      $scope.init null, 'some_model_name'
      expect($scope.modelName).toEqual 'some_model_name'
      expect($scope.filter_opts).toEqual
        status: ''


  describe 'TagCloudCtrl', ->

    it  'should load all tags', inject (Tag)->

      tag = new Tag
        id: 1
        name: 'tag1'
      response = {}
      response[tag.API_FIELDNAME + 's'] = [tag]
      $httpBackend.expectGET "#{tag.BASE_API_URL}?show=text,count"
      .respond 200, angular.toJson(response)
      createController 'TagCloudCtrl', {Tag: Tag}
      $httpBackend.flush()

      expect(({id: x.id, name: x.name} for x in $scope.tag_list)).toEqual [
        id: 1
        name: 'tag1'
      ]

      # handling errors
      $scope.setError = jasmine.createSpy '$scope.setError'
      delete $scope.tag_list
      tag = new Tag
      $httpBackend.expectGET "#{tag.BASE_API_URL}?show=text,count"
      .respond 400
      createController 'TagCloudCtrl', {Tag: Tag}
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalled()
      expect($scope.tag_list).toBeUndefined()


  describe 'AddModelCtl', ->

    it  'should init scope', inject (Model)->
      createController 'AddModelCtl', Model

      expect($scope.formats).toEqual [{name: 'JSON', value: 'json'},
        {name: 'CSV', value: 'csv'}]
      expect
        train_format: $scope.model.train_format
        test_format: $scope.model.test_format
      .toEqual
        train_format: 'json'
        test_format: 'json'


  describe 'UploadModelCtl', ->

    it  'should init scope', inject (Model)->
      createController 'UploadModelCtl', Model

      expect($scope.model).toEqual jasmine.any(Model)


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

      expect($scope.LOADED_SECTIONS).toEqual ['modeljson', 'model', 'main']

      # caching
      $scope.goSection ['model', 'json']
      expect($scope.LOADED_SECTIONS).toEqual ['modeljson', 'model', 'main']

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
      expect($rootScope.setError.calls.mostRecent().args[1]).toEqual 'error starting model training'


  describe 'ModelActionsCtrl', ->

    beforeEach ->
      $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
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
        template: 'partials/servers/choose.html'
        ctrlName: 'ModelUploadToServerCtrl'
      expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope


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
        expect($rootScope.queuedIds).toBeUndefined()

        model = new Model
          id: 999
        downloads = {}
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        $scope.getDataSetsDownloads model.id
        $httpBackend.flush()

        expect($scope.downloads).toEqual downloads
        expect($scope.queuedIds).toEqual []

    it  "should have two downloads", ->
      inject (Model) ->
        createController 'ModelDataSetDownloadCtrl', Model
        expect($scope.queuedIds).toBeUndefined()

        model = new Model
          id: 999
        downloads = [{dataset: {id: 1}, task: {}}, {dataset: {id: 2}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond angular.toJson
          model: model.id
          downloads: downloads

        $scope.getDataSetsDownloads model.id
        $httpBackend.flush()

        expect($scope.downloads).toEqual downloads
        expect($scope.queuedIds.length).toEqual 2
        expect($scope.queuedIds).toEqual [1, 2]

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

        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectPUT(url).respond angular.toJson {dataset: 3}

        $scope.requestDataSetDownload 3
        $httpBackend.flush()

        expect($scope.queuedIds.length).toEqual 3
        expect($scope.queuedIds).toEqual [1, 2, 3]

        # handles request error
        $scope.queuedIds = []
        $scope.setError = jasmine.createSpy('$scope.setError')
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectPUT(url).respond 400

        $scope.requestDataSetDownload 3
        $httpBackend.flush()

        expect($scope.setError.calls.mostRecent().args[1]).toEqual 'requesting dataset 3 for download'
        expect($scope.queuedIds).toEqual []

    it  "should refuse to put new download request", ->
      inject (Model) ->
        model = new Model({id: 777})
        downloads = [{dataset: {id: 1}, task: {}},
          {dataset: {id: 2}, task: {}},
          {dataset: {id: 3}, task: {}}]
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond 200, angular.toJson
          model: model.id
          downloads: downloads

        $scope.setError = jasmine.createSpy()
        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'
        $scope.getDataSetsDownloads()
        $httpBackend.flush()

        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $scope.requestDataSetDownload 3

        expect($scope.setError).toHaveBeenCalledWith({}, 'dataset 3 was already requested for download')

    it  "should set scope error on getting dataset downloads",
      inject (Model) ->
        model = new Model({id: 666})
        url = "#{model.BASE_API_URL}#{model.id}/action/dataset_download/"
        $httpBackend.expectGET(url).respond 400, "{}"
        $scope.setError = jasmine.createSpy()
        $scope.model = model
        createController 'ModelDataSetDownloadCtrl'
        $scope.getDataSetsDownloads()
        $httpBackend.flush()

        expect($scope.setError).toHaveBeenCalled()
