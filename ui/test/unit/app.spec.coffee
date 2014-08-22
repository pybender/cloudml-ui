'use strict'

# jasmine specs for base model go here

describe "base", ->

  beforeEach(module "app")

  $rootScope = null
  settings = null
  $httpBackend = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
  ))

  afterEach( ->
     #$httpBackend.verifyNoOutstandingExpectation()
     #$httpBackend.verifyNoOutstandingRequest()
  )

  describe "$rootScope openDialog", ->
    it "should load model from JSON", inject(($modal) ->
      expect($rootScope.openDialog).toBeDefined()
      handler = {}
      $rootScope.openDialog
        $modal: $modal
        model: handler
        template: 'partials/base/delete_dialog.html'
        ctrlName: 'DeleteImportHandlerCtrl'
        action: 'delete import handler'
        path: "/handlers/" + handler.TYPE
    )
