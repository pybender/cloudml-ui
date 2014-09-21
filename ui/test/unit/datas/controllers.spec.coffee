'use strict'

describe 'app.datas.controllers', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.datas.controllers'
    module 'app.datas.model'
    module 'app.testresults.model'
    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.datasets.model'
    module 'app.features.models'

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

    createController = (ctrl, extras) ->
      $scope = $rootScope.$new()
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)

  afterEach ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()


  describe 'TestExamplesCtrl', ->

    it 'should load an initialize scope with filter options', ->
      createController 'TestExamplesCtrl'
      expect($scope.filter_opts).toBeDefined()
      expect($scope.simple_filters).toEqual {}
      expect($scope.data_filters).toEqual []
      expect($scope.loading_state).toBe false
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true

      $location.search({sort_by: 'something', order: 'desc'})
      createController 'TestExamplesCtrl'
      expect($scope.filter_opts).toEqual {sort_by: 'something', order: 'desc'}
      expect($scope.simple_filters).toEqual {}
      expect($scope.data_filters).toEqual []
      expect($scope.loading_state).toBe false
      expect($scope.sort_by).toEqual 'something'
      expect($scope.asc_order).toBe false

    describe 'loading test and model with handling http errors', ->

      beforeEach ->
        $rootScope.setError = jasmine.createSpy '$rootScope.setError'

      test = null
      model = null
      prepareHttp = (test, model, failTestGET, failModelGET) ->
        createController 'TestExamplesCtrl'

        $scope.init test
        expect($scope.loading_state).toBe true

        if failTestGET
          respondArgs = [400]
        else
          response = {}
          response[test.API_FIELDNAME] = test
          respondArgs = [200, angular.toJson response]
        $httpBackend.expectGET "#{test.BASE_API_URL}#{test.id}/?show=name,examples_fields"
        .respond respondArgs...

        if failModelGET
          respondArgs = [400]
        else
          response = {}
          response[model.API_FIELDNAME] = model
          respondArgs = [200, angular.toJson response]
        $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=name,labels"
        .respond respondArgs...
        $httpBackend.flush()

      it 'should process filter options to build form', inject (TestResult, Model)->
        test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
        model = new Model {id: test.model_id, labels: ['label1', 'label2']}

        $location.search
          'data_input->>fieldA': 'fieldAValue'
          'label': 'somelable'
          'pred_label': 'soomepred_label'
        prepareHttp test, model, false, false

        expect($scope.data_filters).toEqual [{name: 'data_input->>fieldA', value: 'fieldAValue'}]
        expect($scope.simple_filters).toEqual
          label: 'somelable'
          pred_label: 'soomepred_label'
          'data_input->>fieldA': 'fieldAValue'
          action: 'examples:list'

      it 'should load test data test GET success, model GET success', inject (TestResult, Model)->
        test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
        model = new Model {id: test.model_id, labels: ['label1', 'label2']}
        prepareHttp test, model, false, false

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual test
        expect($scope.fields).toEqual ['fieldA', 'fieldB']
        expect($scope.loading_state).toBe false
        expect($scope.model.id).toEqual model.id
        expect($scope.labels).toEqual ['label1', 'label2']

      it 'should load test data test GET fail, model GET success', inject (TestResult, Model)->
        test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
        model = new Model {id: test.model_id, labels: ['label1', 'label2']}
        prepareHttp test, model, true, false

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual test
        expect($scope.fields).toBeUndefined()
        expect($scope.loading_state).toBe false
        expect($scope.model.id).toEqual model.id
        expect($scope.labels).toEqual ['label1', 'label2']

        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test details'

      it 'should load test data test GET success, model GET fail', inject (TestResult, Model)->
        test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
        model = new Model {id: test.model_id, labels: ['label1', 'label2']}
        prepareHttp test, model, false, true

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual test
        expect($scope.fields).toEqual ['fieldA', 'fieldB']
        expect($scope.loading_state).toBe false
        expect($scope.model.id).toEqual model.id
        expect($scope.labels).toBeUndefined()

        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading model'

      it 'should load test data test GET fail, model GET fail', inject (TestResult, Model)->
        test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
        model = new Model {id: test.model_id, labels: ['label1', 'label2']}
        prepareHttp test, model, true, true

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual test
        expect($scope.fields).toBeUndefined()
        expect($scope.loading_state).toBe false
        expect($scope.model.id).toEqual model.id
        expect($scope.labels).toBeUndefined()

        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading model'
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test details'

    it 'should load data with and without filter options', inject (TestResult, Data)->

      createController 'TestExamplesCtrl'
      test = new TestResult {id: 999, model_id: 888, examples_fields: ['fieldA', 'fieldB']}
      $scope.test = test
      $scope.loadDatas()({})

      d1 = new Data {id: 777, model_id: test.model_id, test_id: test.id}
      d2 = new Data {id: 777, model_id: test.model_id, test_id: test.id}
      response = {}
      response[d1.API_FIELDNAME + 's'] = [d1, d2]
      $httpBackend.expectGET "#{d1.BASE_API_URL}?order=asc&show=id,name,label,pred_label,title,prob,example_id&sort_by="
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.loading_state).toBe false

      # with some filter options
      $scope.sort_by = 'sortby_zinger'
      $scope.asc_order = false
      $scope.loadDatas()({filter_opts: 'filter_opts', option1: 'option1'})
      $httpBackend.expectGET "#{d1.BASE_API_URL}?option1=option1&order=desc&show=id,name,label,pred_label,title,prob,example_id&sort_by=sortby_zinger"
      .respond 200, angular.toJson response
      $httpBackend.flush()

      # handling errors
      $scope.sort_by = ''
      $scope.asc_order = true
      $scope.loadDatas()({})
      $httpBackend.expectGET "#{d1.BASE_API_URL}?order=asc&show=id,name,label,pred_label,title,prob,example_id&sort_by="
      .respond 400
      $httpBackend.flush()

      expect($scope.loading_state).toBe false

    it 'should change sort configuration', ->
      createController 'TestExamplesCtrl'

      # this is just to avoid the @load that I don't know about
      $scope.load = jasmine.createSpy '$scope.load'

      # switching sort order
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual {}
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe false
      expect($location.search()).toEqual { sort_by : '', order : 'desc' }
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual { sort_by : '', order : 'asc' }

      # changing sort_by, but first let's reset
      $scope.sort($scope.sort_by)
      expect($scope.sort_by).toEqual ''
      expect($scope.asc_order).toBe false
      expect($location.search()).toEqual { sort_by : '', order : 'desc' }
      $scope.sort('zinger')
      expect($scope.sort_by).toEqual 'zinger'
      expect($scope.asc_order).toBe true
      expect($location.search()).toEqual { sort_by : 'zinger', order : 'asc' }

    it 'should add filter', ->
      createController 'TestExamplesCtrl'

      expect($scope.data_filters).toEqual []

      $scope.addFilter()
      expect($scope.data_filters).toEqual [{name: '', value: ''}]

    it 'should change filter configuration', ->
      createController 'TestExamplesCtrl'

      $scope.data_filters = [{name: 'filter1_name', value: 'filter1_value'},
      {name: 'filter2_name', value: 'filter2_value'}]
      $scope.filter()

      expect($scope.filter_opts).toEqual {filter1_name: 'filter1_value', filter2_name: 'filter2_value'}
      expect($location.search()).toEqual {sort_by : '', order: 'asc', filter1_name: 'filter1_value', filter2_name: 'filter2_value'}

    it 'should go to example details', inject (Data)->

      createController 'TestExamplesCtrl'

      d = new Data {id:999, model_id: 888, test_id: 777}
      $scope.details d
      expect($location.url()).toEqual '/models/888/tests/777/examples/999?sort_by=&order=asc'

    it 'should build parameters dict', ->

      createController 'TestExamplesCtrl'

      expect($scope.getParamsDict()).toEqual {sort_by : '', order: 'asc'}

      $scope.filter_opts = {filter1_name: 'filter1_value', action: 'some_action'}
      $scope.sort_by = 'some-field'
      $scope.asc_order = false

      expect($scope.getParamsDict()).toEqual {sort_by: 'some-field', order: 'desc', filter1_name: 'filter1_value'}

    it 'should build example url', inject (Data)->
      createController 'TestExamplesCtrl'

      d = new Data {id:999, model_id: 888, test_id: 777}
      expect($scope.getExampleUrl d).toEqual '/models/888/tests/777/examples/999?sort_by=&order=asc'


  describe 'GroupedExamplesCtrl', ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should initialize scope and load test', inject (TestResult)->

      $routeParams = {model_id: 999, test_id: 888}

      createController 'GroupedExamplesCtrl', {$routeParams: $routeParams}
      expect($scope.loading_state).toBe true
      expect($scope.form).toEqual = {'field': "", 'count': 2 }
      expect($scope.loading_state).toBe true
      expect($scope.test.id).toEqual $routeParams.test_id
      expect($scope.test.model_id).toEqual $routeParams.model_id

      test = new TestResult {id: $routeParams.test_id, model_id: $routeParams.model_id}
      response = {}
      response[test.API_FIELDNAME] = test
      $httpBackend.expectGET "#{test.BASE_API_URL}#{test.id}/?show=name,examples_fields"
      .respond 200, angular.toJson response
      $httpBackend.flush()
      expect($scope.loading_state).toBe false

      # test load error
      createController 'GroupedExamplesCtrl', {$routeParams: $routeParams}
      $httpBackend.expectGET "#{test.BASE_API_URL}#{test.id}/?show=name,examples_fields"
      .respond 400
      $httpBackend.flush()
      expect($scope.loading_state).toBe true
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test details'

    it 'should update groups', inject (TestResult, Data)->
      $routeParams = {model_id: 999, test_id: 888}

      createController 'GroupedExamplesCtrl', {$routeParams: $routeParams}
      test = new TestResult {id: $routeParams.test_id, model_id: $routeParams.model_id}
      response = {}
      response[test.API_FIELDNAME] = test
      $httpBackend.expectGET "#{test.BASE_API_URL}#{test.id}/?show=name,examples_fields"
      .respond 200, angular.toJson response
      $httpBackend.flush()

      $scope.update()
      expect($scope.setError).toHaveBeenCalledWith {}, 'Please, select a field'

      $scope.form = {field: 'the_field', count: 1}
      $scope.update()
      expect($scope.loading_state).toBe true

      d1 = new Data {id: 777, test_id: $routeParams.test_id, model_id: $routeParams.model_id}
      d2 = new Data {id: 666, test_id: $routeParams.test_id, model_id: $routeParams.model_id}
      response = {field_name: 'should_be_the_field', mavp: 'dont know what is that'}
      response[d1.API_FIELDNAME + 's'] = {items: [d1, d2]}
      $httpBackend.expectGET "#{d1.BASE_API_URL}action/groupped/?count=1&field=the_field"
      .respond 200, angular.toJson response
      $httpBackend.flush()

      expect($scope.field_name).toEqual 'should_be_the_field'
      expect($scope.mavp).toEqual 'dont know what is that'
      expect([{id: x.id} for x in $scope.objects]).toEqual [[{id: 777}, {id: 666}]]
      expect($scope.loading_state).toBe false

      # http error
      createController 'GroupedExamplesCtrl', {$routeParams: $routeParams}
      test = new TestResult {id: $routeParams.test_id, model_id: $routeParams.model_id}
      $httpBackend.expectGET "#{test.BASE_API_URL}#{test.id}/?show=name,examples_fields"
      .respond 400
      $httpBackend.flush()

      $scope.form = {field: 'the_field', count: 1}
      $scope.update()
      expect($scope.loading_state).toBe true

      $httpBackend.expectGET "#{d1.BASE_API_URL}action/groupped/?count=1&field=the_field"
      .respond 400
      $httpBackend.flush()

      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test examples'
      expect($scope.loading_state).toBe false


  describe 'ExampleDetailsCtrl', ->

    beforeEach ->
      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

    it 'should initialize scope and call goSection', inject (Data)->

      $routeParams = {id: 777, model_id: 999, test_id: 888}

      $location.search({filter_name: 'filter_value'})
      createController 'ExampleDetailsCtrl', {$routeParams: $routeParams}

      expect($scope.filter_opts).toEqual {filter_name: 'filter_value'}
      expect($scope.loaded).toBe false

      d1 = new Data $routeParams

      # error in http
      $scope.goSection()
      $httpBackend.expectGET "#{d1.BASE_API_URL}#{d1.id}/?filter_name=filter_value&show=test_name,weighted_data_input,model,pred_label,label,prob,created_on,test_result,next,previous,parameters_weights,data_input"
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test example'
      expect($scope.loaded).toBe false

      $scope.goSection()
      response = {}
      response[d1.API_FIELDNAME] = d1
      $httpBackend.expectGET "#{d1.BASE_API_URL}#{d1.id}/?filter_name=filter_value&show=test_name,weighted_data_input,model,pred_label,label,prob,created_on,test_result,next,previous,parameters_weights,data_input"
      .respond 200, angular.toJson response
      $httpBackend.flush()
      expect($scope.loaded).toBe true

    it 'should respond to next,previous and back', inject (Data)->
      $routeParams = {id: 777, model_id: 999, test_id: 888}
      $location.search({filter_name: 'filter_value'})
      createController 'ExampleDetailsCtrl', {$routeParams: $routeParams}

      $scope.data = new Data _.extend($routeParams, {next: 666, previous: 555})

      $scope.next()
      expect($location.url()).toEqual '/models/999/tests/888/examples/666?filter_name=filter_value'

      $scope.previous()
      expect($location.url()).toEqual '/models/999/tests/888/examples/555?filter_name=filter_value'

      $scope.back()
      expect($location.url()).toEqual '/models/999/tests/888?action=examples:list&filter_name=filter_value'

      $scope.data = {}
      expect ->
        $scope.redir {}
      .toThrow new Error('ERR: Prev or Next should be disabled!')


  describe "CsvDownloadCtrl", ->

    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      $rootScope.$close = jasmine.createSpy '$rootScope.$close'

    it "should load data fields", inject (TestResult, Data) ->

      test = new TestResult {id: 888, model_id: 777}
      data = new Data {id: 666, model_id: test.model_id, test_id: test.id}

      openOptions = {model: test}
      createController "CsvDownloadCtrl", {'openOptions': openOptions}

      expect($scope.csvField).toEqual ''
      expect($scope.stdFields).toEqual ['label', 'pred_label', 'prob']
      expect($scope.extraFields).toEqual []
      expect($scope.loading_state).toBe true

      # error the data load
      $httpBackend.expectGET "#{data.BASE_API_URL}action/datafields/"
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading data field list'
      expect($scope.loading_state).toBe false
      $scope.setError.calls.reset()

      createController "CsvDownloadCtrl", {'openOptions': openOptions}
      $httpBackend.expectGET "#{data.BASE_API_URL}action/datafields/"
      .respond('{"fields": ["2two", "1one", "4four", "3three"]}')
      $httpBackend.flush()

      # retrieve fields without reordering
      expect($scope.extraFields).toEqual(['2two', '1one', '4four', '3three'])
      expect($scope.selectFields).toEqual []
      expect($scope.loading_state).toBe false

      # removing a field
      $scope.removeField '4four'
      expect($scope.extraFields).toEqual(['2two', '1one', '3three'])
      expect($scope.selectFields).toEqual ['4four']

      # removing a field (again just to make sure)
      $scope.removeField '4four'
      expect($scope.extraFields).toEqual(['2two', '1one', '3three'])
      expect($scope.selectFields).toEqual ['4four']

      # removing another field, should reorder selectFields
      $scope.removeField '1one'
      expect($scope.extraFields).toEqual(['2two', '3three'])
      expect($scope.selectFields).toEqual ['1one', '4four']

      # append a field
      $scope.csvField = '1one'
      $scope.appendField('1one')
      expect($scope.extraFields).toEqual(['2two', '3three', '1one'])
      expect($scope.selectFields).toEqual ['4four']

      # append the same field again
      $scope.csvField = '1one'
      $scope.appendField('1one')
      expect($scope.extraFields).toEqual(['2two', '3three', '1one'])
      expect($scope.selectFields).toEqual ['4four']

      # append a bogus
      $scope.csvField = 'bogus'
      $scope.appendField('bogus')
      expect($scope.extraFields).toEqual(['2two', '3three', '1one'])
      expect($scope.selectFields).toEqual ['4four']

      # remove all
      $scope.removeAll()
      expect($scope.extraFields).toEqual([])
      expect($scope.selectFields).toEqual ['1one', '2two', '3three', '4four']

      # add all
      $scope.addAll()
      expect($scope.extraFields).toEqual(['1one', '2two', '3three', '4four'])
      expect($scope.selectFields).toEqual []

    it 'should put csv export', inject (Data, TestResult)->
      test = new TestResult {id: 888, model_id: 777}
      data = new Data {id: 666, model_id: test.model_id, test_id: test.id}

      openOptions = {model: test}
      createController "CsvDownloadCtrl", {'openOptions': openOptions}
      $httpBackend.expectGET "#{data.BASE_API_URL}action/datafields/"
      .respond('{"fields": ["2two", "1one", "4four", "3three"]}')
      $httpBackend.flush()

      # get csv
      $scope.getExamplesCsv()

      $httpBackend.expectPUT "#{data.BASE_API_URL}action/csv_task/"
      .respond("{\"url\":\"#{data.BASE_API_URL}\"}")
      $httpBackend.flush()

      expect($scope.loading_state).toBe false
      expect($location.search()).toEqual {action : 'about:details'}
      expect($scope.$close).toHaveBeenCalledWith true

      # get csv, something went bad
      $scope.getExamplesCsv()
      $httpBackend.expectPUT("#{data.BASE_API_URL}action/csv_task/").respond(400)
      $httpBackend.flush()
      expect($scope.loading_state).toBe false
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'failed submitting csv generation request'

    it 'should put db export', inject (Data, TestResult)->
      test = new TestResult {id: 888, model_id: 777}
      data = new Data {id: 666, model_id: test.model_id, test_id: test.id}

      openOptions = {model: test}
      createController "CsvDownloadCtrl", {'openOptions': openOptions}
      $httpBackend.expectGET "#{data.BASE_API_URL}action/datafields/"
      .respond('{"fields": ["2two", "1one", "4four", "3three"]}')
      $httpBackend.flush()

      # get csv
      $scope.exportExamplesToDb()

      $httpBackend.expectPUT "#{data.BASE_API_URL}action/db_task/"
      .respond("{\"url\":\"#{data.BASE_API_URL}\"}")
      $httpBackend.flush()

      expect($scope.loading_state).toBe false
      expect($location.search()).toEqual {action : 'about:details'}
      expect($scope.$close).toHaveBeenCalledWith true

      # get csv, something went bad
      $scope.exportExamplesToDb()
      $httpBackend.expectPUT("#{data.BASE_API_URL}action/db_task/").respond(400)
      $httpBackend.flush()
      expect($scope.loading_state).toBe false
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'failed submitting export to db request'
