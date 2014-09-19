describe 'xml_importhandlers/controllers/entities', ->
  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.controllers.entities'
    module 'app.xml_importhandlers.models'

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
      inject (ImportHandler, Query)->
        $rootScope.openDialog = jasmine.createSpy '$rootScope.openDialog'
        handler = new ImportHandler
          id: 999
          name: 'import handelr'
        query = new Query
          id: 888

        url = "#{handler.BASE_API_URL}#{handler.id}"

        $rootScope.handler = handler
        createController "EntitiesTreeCtrl"

        $scope.runQuery query
        expect($scope.openDialog).toHaveBeenCalledWith jasmine.any(Object),
          model: null
          template: 'partials/import_handler/test_query.html'
          ctrlName: 'QueryTestDialogCtrl'
          extra:
            handlerUrl: url
            datasources: handler.xml_data_sources
            query: query
          action: 'test xml import handler query'
        expect($scope.openDialog.calls.mostRecent().args[0]).toEqual $scope

