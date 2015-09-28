'use strict'

describe 'app.datas.controllers', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app'
    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.datas.controllers'
    module 'app.datas.model'
    module 'app.testresults.model'
    module 'app.models.model'
    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
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

  $base_url = null
  $test = null
  $model = null
  $data_fields_url = null
  $data_fields_response = {"fields": ["data_input->total", "data_input->country"]}

  beforeEach inject (Model, TestResult) ->
    $routeParams = {model_id: 999, test_id: 888}
    $test = new TestResult {id: $routeParams.test_id, model_id: $routeParams.model_id}
    $model = new Model {id: $test.model_id, labels: ['yes', 'no']}
    $base_url = $test.BASE_API_URL + $test.id
    $data_fields_url = $base_url + "/examples/action/datafields/"

  describe 'TestExamplesCtrl (Examples List tab)', ->
    describe 'TestExamplesCtrl creating', ->

      it 'should load an initialize scope with default values', ->
        createController 'TestExamplesCtrl'
        expect($scope.filter_opts).toBeDefined()
        expect($scope.simple_filters).toEqual {}
        expect($scope.data_filters).toEqual {}
        expect($scope.sort_by).toEqual ''
        expect($scope.asc_order).toBe true

      it 'should load an initialize scope with values from query string', ->
        $location.search({sort_by: 'the_field', order: 'desc'})
        createController 'TestExamplesCtrl'
        expect($scope.filter_opts).toEqual {sort_by: 'the_field', order: 'desc'}
        expect($scope.simple_filters).toEqual {}
        expect($scope.data_filters).toEqual {}
        expect($scope.sort_by).toEqual 'the_field'
        expect($scope.asc_order).toBe false

    describe 'TestExamplesCtrl.init', ->

      beforeEach ->
        $rootScope.setError = jasmine.createSpy '$rootScope.setError'
     
      prepareHttp = (test, model, failDataFieldsGET, failLabelsGET) ->
        createController 'TestExamplesCtrl'

        $scope.init test

        # initializing data filters
        if failDataFieldsGET
          respondArgs = [400]
        else
          respondArgs = [200, angular.toJson $data_fields_response]

        $httpBackend.expectGET $data_fields_url
        .respond respondArgs...

        # Initializing model's labels (target_variables values)
        if failLabelsGET
          respondArgs = [400]
        else
          response = {}
          response[model.API_FIELDNAME] = model
          respondArgs = [200, angular.toJson response]
        $httpBackend.expectGET "#{model.BASE_API_URL}#{model.id}/?show=name,labels"
        .respond respondArgs...

        $httpBackend.flush()

      it 'should initialize form filters', inject (TestResult, Model)->
        $location.search
          'data_input->country': 'Australia'
          'label': 'yes'
          'pred_label': 'no'
        prepareHttp $test, $model, false, false

        # Checking whether filters was properly constructed
        expect($scope.data_filters).toEqual
          "data_input->country" : 'Australia'
        expect($scope.simple_filters).toEqual
          label: 'yes'
          pred_label: 'no'

        expect($scope.fields).toEqual $data_fields_response.fields
        expect($scope.labels).toEqual $model.labels
        expect($scope.model.id).toEqual $model.id
        expect($scope.test.id).toEqual $test.id
        expect($scope.extra_params).toEqual {action: 'examples:list'}

      it 'should does not include unexistant data filters', inject (TestResult, Model)->
        $location.search
          'data_input->country': 'Australia'
          'data_input->unexistant': 'value1'
          'unexistant_filter': 'value2'
          'label': 'yes'
          'pred_label': 'no'
        prepareHttp $test, $model, false, false

        # Checking whether filters was properly constructed
        expect($scope.data_filters).toEqual
          "data_input->country" : 'Australia'
        expect($scope.simple_filters).toEqual
          label: 'yes'
          pred_label: 'no'

      it 'should load data fields GET fail, model labels GET success', ->
        prepareHttp $test, $model, true, false

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual $test
        expect($scope.model.id).toEqual $model.id
        expect($scope.labels).toEqual $model.labels

        # Checking the error initializing data fields
        expect($scope.fields).toBeUndefined()
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading data field list'

      it 'should load data fields GET success, model labels GET fail', ->
        prepareHttp $test, $model, false, true

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual $test
        expect($scope.fields).toEqual $data_fields_response.fields
        expect($scope.model.id).toEqual $model.id

        # Checking model labels loading error
        expect($scope.labels).toBeUndefined()
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading model labels'

      it 'should load data fields GET fail, model labels GET fail', ->
        prepareHttp $test, $model, true, true

        expect($scope.extra_params).toEqual {action: 'examples:list'}
        expect($scope.test).toEqual $test
        expect($scope.model.id).toEqual $model.id

        # Checking loading error
        expect($scope.fields).toBeUndefined()
        expect($scope.labels).toBeUndefined()
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading model labels'
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading data field list'

    it 'should load data with and without filter options', inject (TestResult, Data)->

      createController 'TestExamplesCtrl'
      test = $scope.test = $test
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

    it 'should change query string when init data filters', ->
      createController 'TestExamplesCtrl'
      data_filters =
        "data_input->country" : 'Australia'
        "data_input->total" : 10

      $scope.data_filters = data_filters
      $scope.filter()

      expect($scope.filter_opts).toEqual data_filters
      expect($location.search()).toEqual _.extend(data_filters, {sort_by : '', order: 'asc'})

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


  describe 'GroupedExamplesCtrl (Average Precision Page)', ->
    beforeEach ->
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'

      createController 'GroupedExamplesCtrl', {$routeParams: $routeParams}
      expect($scope.form).toEqual = {'field': "", 'count': 2 }

    it 'should initialize scope and load data fields',  ->
      $httpBackend.expectGET $data_fields_url
      .respond 200, angular.toJson $data_fields_response
      $httpBackend.flush()

    it 'should show error message when have bad request while loading data fields', ->
      $httpBackend.expectGET $data_fields_url
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading data field list'

    describe 'GroupedExamplesCtrl.update', ->
      $form = {count: 2, field: 'data_input->country'}
      $average_precision_url = null
      $average_precision_response = null
      $avp_items = null

      beforeEach inject ($injector) ->
        Data = $injector.get 'Data'
        $httpBackend.expectGET $data_fields_url
        .respond 200, angular.toJson $data_fields_response
        $httpBackend.flush()
        
        test_example = new Data _.extend($routeParams, {id: 777})
        $average_precision_response = {
          field_name: $form.field
          mavp: 0.9
        }
        $avp_items = [
          {"count": 60, "avp": 1.0, "group_by_field": "United States"},
          {"count": 9, "avp": 0.89, "group_by_field": "Australia"}
        ]
        $average_precision_response[test_example.API_FIELDNAME + 's'] = {
          items: $avp_items
        }
        $average_precision_url = test_example.BASE_API_URL + "action/groupped/?" + $.param($form)

      it "should calculate average precision", inject (Data) ->
        $scope.form = $form
        $scope.update()

        $httpBackend.expectGET $average_precision_url
        .respond 200, angular.toJson $average_precision_response
        $httpBackend.flush()

        expect($scope.field_name).toEqual $form.field
        expect($scope.mavp).toEqual $average_precision_response['mavp']
        expect($scope.objects).toEqual $avp_items

      it "should show an error message, when have bad request while calc avp", ->
        $scope.form = $form
        $scope.update()

        $httpBackend.expectGET $average_precision_url
        .respond 400
        $httpBackend.flush()
        expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading grouped test examples'


  describe 'ExampleDetailsCtrl', ->

    beforeEach ->
      $rootScope.initSections = jasmine.createSpy '$rootScope.initSections'
      $rootScope.setError = jasmine.createSpy '$rootScope.setError'
      $routeParams = _.extend($routeParams, {id: 777})

    it 'should initialize scope and call goSection', inject (Data)->
      d1 = new Data $routeParams

      $location.search({filter_name: 'filter_value'})
      createController 'ExampleDetailsCtrl', {$routeParams: $routeParams}

      expect($scope.filter_opts).toEqual {filter_name: 'filter_value'}
      expect($scope.loaded).toBe false

      fields = ['test_name', 'weighted_data_input', 'model',
                'pred_label', 'label', 'prob', 'created_on',
                'test_result', 'next', 'previous', 'parameters_weights',
                'data_input', 'name'].join(',')
      url = d1.BASE_API_URL + "#{d1.id}/?filter_name=filter_value&show=" + fields

      # error in http
      $scope.goSection()      
      $httpBackend.expectGET url
      .respond 400
      $httpBackend.flush()
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'loading test example'
      expect($scope.loaded).toBe false

      $scope.goSection()
      response = {}
      response[d1.API_FIELDNAME] = d1
      $httpBackend.expectGET url
      .respond 200, angular.toJson response
      $httpBackend.flush()
      expect($scope.loaded).toBe true

    it 'should respond to next,previous and back', inject (Data)->
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

      $httpBackend.expectPUT "#{data.BASE_API_URL}action/csv_task/", (data)->
        return angular.toJson(data.getData()) is angular.toJson({fields: '["label","pred_label","prob","2two","1one","4four","3three"]'})
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
      expect($scope.extraData).toBeDefined()

      $httpBackend.expectGET "#{data.BASE_API_URL}action/datafields/"
      .respond('{"fields": ["2two", "1one", "4four", "3three"]}')
      $httpBackend.flush()

      # get db
      $scope.extraData = {datasource: 'ds1', tablename: 'tablename2'}
      $scope.exportExamplesToDb()

      $httpBackend.expectPUT "#{data.BASE_API_URL}action/db_task/", (data)->
        return angular.toJson(data.getData()) is angular.toJson({fields: '["label","pred_label","prob","2two","1one","4four","3three"]',
        datasource: 'ds1', tablename: 'tablename2'})
      .respond("{\"url\":\"#{data.BASE_API_URL}\"}")
      $httpBackend.flush()

      expect($scope.loading_state).toBe false
      expect($location.search()).toEqual {action : 'about:details'}
      expect($scope.$close).toHaveBeenCalledWith true

      # get db, something went bad
      $scope.exportExamplesToDb()
      $httpBackend.expectPUT("#{data.BASE_API_URL}action/db_task/").respond(400)
      $httpBackend.flush()
      expect($scope.loading_state).toBe false
      expect($scope.setError).toHaveBeenCalledWith jasmine.any(Object), 'failed submitting export to db request'
