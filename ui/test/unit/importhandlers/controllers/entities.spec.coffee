describe 'xml_importhandlers/controllers/entities', ->
  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.models'
    module 'app.importhandlers.xml.models'
    module 'app.importhandlers.xml.controllers.entities'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  $modal = null
  createController = null
  $scope = null
  $timeout = null
  $window = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')
    $modal = $injector.get('$modal')
    $timeout = $injector.get('$timeout')
    $window = $injector.get('$window')

    $scope = $rootScope.$new()
    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach( ->
    $httpBackend.verifyNoOutstandingExpectation()
    $httpBackend.verifyNoOutstandingRequest()
  )


  describe "EntitiesTreeCtrl", ->
    it "Should call open dialog for runQuery with proper arguments",
      inject (XmlImportHandler, XmlQuery)->
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        handler = new XmlImportHandler
          id: 999
          name: 'import handelr'
        query = new XmlQuery
          id: 888

        url = "#{handler.BASE_API_URL}#{handler.id}"

        $rootScope.handler = handler
        createController "EntitiesTreeCtrl"

        $scope.runQuery query
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: null
          template: 'partials/importhandlers/test_query.html'
          ctrlName: 'QueryTestDialogCtrl'
          extra:
            handlerUrl: url
            datasources: handler.xml_data_sources
            query: query
          action: 'test xml import handler query'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

    it "Should call open dialog for getting pig fields with proper args",
      inject (XmlImportHandler, Sqoop)->
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        handler = new XmlImportHandler
          id: 999
          name: 'import handelr'
        sqoop = new Sqoop
          id: 888

        $rootScope.handler = handler
        createController "EntitiesTreeCtrl"

        $scope.getPigFields sqoop
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: sqoop
          template: 'partials/importhandlers/xml/sqoop/load_pig_fields.html'
          ctrlName: 'PigFieldsLoader'
          extra: {noInput: false, title: 'Pig Fields'}

        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

  describe "PigFieldsLoader", ->
    it "Should request pig query generation for sqoop script",
      inject (XmlImportHandler, Sqoop)->
        sqoop = new Sqoop
          id: 888
          import_handler_id: 999
          entity_id: 555
        openOptions = {'model': sqoop}
        createController "PigFieldsLoader", {'openOptions': openOptions}
        $scope.getFields()

        url = Sqoop.$get_api_url({}, sqoop)
        $httpBackend.expectPUT "#{url}#{sqoop.id}/action/pig_fields/"
        .respond 200, angular.toJson {'fields': {}, 'sample': 'pig_data', 'sql': 'sql...'}
        $httpBackend.flush()
