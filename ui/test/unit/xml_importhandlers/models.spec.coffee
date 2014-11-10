'use strict'

describe 'app.xml_importhandlers.models', ->

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'

    module 'app.base'
    module 'app.config'
    module 'app.services'

    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'

  $httpBackend = null
  $rootScope = null
  settings = null
  $routeParams = null
  $location = null
  createController = null
  $scope = null

  beforeEach(inject(($injector) ->
    settings = $injector.get('settings')
    $httpBackend = $injector.get('$httpBackend')
    $rootScope = $injector.get('$rootScope')
    $controller = $injector.get('$controller')
    $routeParams = $injector.get('$routeParams')
    $location = $injector.get('$location')

    $scope = $rootScope.$new()
    createController = (ctrl, extras) ->
      injected = extras or {}
      _.extend injected, {'$scope' : $scope }
      $controller(ctrl, injected)
  ))

  afterEach ->
     $httpBackend.verifyNoOutstandingExpectation()
     $httpBackend.verifyNoOutstandingRequest()


  describe 'BaseImportHandlerItem Model', ->

    it 'should have BaseImportHandlers properties and methods defined', inject (BaseImportHandlerItem)->

      expect(BaseImportHandlerItem.ITEM_NAME).toEqual 'item'
      expect(BaseImportHandlerItem.$get_api_url).toEqual jasmine.any(Function)
      expect(BaseImportHandlerItem.$beforeLoadAll).toEqual jasmine.any(Function)

    describe 'class methods to function properly', ->

      it 'should have $get_api_url to work with model and options', inject (BaseImportHandlerItem)->

        # model value take precedence over opts
        expect BaseImportHandlerItem.$get_api_url {import_handler_id: 111}, {import_handler_id: 222}
        .toEqual "#{settings.apiUrl}xml_import_handlers/222/#{BaseImportHandlerItem.ITEM_NAME}/"

        # fallback to opts
        expect BaseImportHandlerItem.$get_api_url {import_handler_id: 111}
        .toEqual "#{settings.apiUrl}xml_import_handlers/111/#{BaseImportHandlerItem.ITEM_NAME}/"

        # throws
        expect ->
          BaseImportHandlerItem.$get_api_url {}
        .toThrow new Error "import_handler_id:undefined should be defined"

      it 'should have $beforeLoadAll to work with opts or throw exception', inject (BaseImportHandlerItem)->

        expect BaseImportHandlerItem.$beforeLoadAll
        .toThrow new Error "import_handler_id is required"

        expect ->
          BaseImportHandlerItem.$beforeLoadAll({})
        .toThrow new Error "import_handler_id is required"


  describe 'XmlImportHandler Model', ->

    it 'should have XmlImportHandler properties and methods defined', inject (XmlImportHandler)->

      expect(XmlImportHandler.LIST_MODEL_NAME).toEqual 'xml_import_handlers'
      expect(XmlImportHandler.MAIN_FIELDS).toEqual 'id,name,created_on,created_by,updated_on,updated_by'

    it 'can create an instance with predefined properties set', inject (XmlImportHandler)->
      handler = new XmlImportHandler
      expect(handler.BASE_API_URL).toEqual "#{settings.apiUrl}xml_import_handlers/"
      expect(handler.BASE_UI_URL).toEqual "/handlers/xml"
      expect(handler.API_FIELDNAME).toEqual 'xml_import_handler'
      expect(handler.LIST_MODEL_NAME).toEqual XmlImportHandler.LIST_MODEL_NAME
      expect(handler.TYPE).toEqual 'XML'
      expect(handler.id).toBe null
      expect(handler.name).toBe null
      expect(handler.created_on).toBe null
      expect(handler.created_by).toBe null
      expect(handler.xml_input_parameters).toEqual []
      expect(handler.scripts).toEqual []
      expect(handler.entities).toEqual []
      expect(handler.predict).toEqual []

    it 'constructor filled up', inject (XmlImportHandler)->

      handler = new XmlImportHandler {id: 111, name: 'test'}

      expect(handler.id).toEqual 111
      expect(handler.name).toEqual 'test'
      expect(handler.entities).toEqual []
      expect(handler.xml_input_parameters).toEqual []

    it 'constructor filled up with entities and input parameters', inject (XmlImportHandler)->

      handler = new XmlImportHandler
        id: 111
        name: 'test'
        entity: {id: 333, name: 'entity333'}
        xml_input_parameters: [{id: 444, name: 'input444'}, {id: 555, name: 'input555'}]

      expect(handler.id).toEqual 111
      expect(handler.name).toEqual 'test'
      expect(handler.entities).toEqual [] # this quite strange why do we need entities?
      expect({id: handler.entity.id, name: handler.entity.name, import_handler_id: handler.entity.import_handler_id})
      .toEqual {id: 333, name: 'entity333', import_handler_id: 111}
      expect(({id: x.id, name:x.name, import_handler_id: x.import_handler_id} for x in handler.xml_input_parameters))
      .toEqual [{id: 444, name: 'input444', import_handler_id: 111}, {id: 555, name: 'input555', import_handler_id: 111}]

    describe 'class methods to function properly', ->

      it 'should upload to predict', inject (XmlImportHandler)->
        handler = new XmlImportHandler {id: 111, name: 'test'}
        url = "#{handler.BASE_API_URL}#{handler.id}/action/upload_to_server/"
        $httpBackend.expectPUT(url).respond 400
        spyOn(handler, '$make_request').and.callThrough()
        server = {name: 'some_server'}
        handler.$uploadPredict(server)
        $httpBackend.flush()

        expect(handler.$make_request).toHaveBeenCalledWith url, {}, "PUT", {'server': server}


  describe 'Field Model', ->

    it 'should have Field properties and methods defined', inject (Field)->

      expect(Field.LIST_MODEL_NAME).toEqual 'fields'
      expect(Field.MAIN_FIELDS).toEqual 'id,name'

    it 'can create an instance with predefined properties set', inject (Field)->
      field = new Field
      expect(field.BASE_API_URL).toEqual "#{settings.apiUrl}xml_import_handlers/fields/"
      expect(field.API_FIELDNAME).toEqual 'xml_field'
      expect(field.LIST_MODEL_NAME).toEqual Field.LIST_MODEL_NAME
      expect(field.TYPES_LIST).toEqual ['integer', 'boolean', 'string', 'float', 'json']
      expect(field.TRANSFORM_LIST).toEqual ['csv', 'json']
      expect(field.id).toBe null

    it 'constructor filled up', inject (Field)->

      field = new Field {id: 111, name: 'test_field'}

      expect(field.id).toEqual 111
      expect(field.name).toEqual 'test_field'

    describe 'class methods to function properly', ->

      it 'should have $get_api_url to work with model and options', inject (Field)->

        opts = {import_handler_id: 111, entity_id: 333}
        model = {import_handler_id: 222, entity_id: 444}

        # model value take precedence over opts
        expect Field.$get_api_url opts, model
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{model.import_handler_id}/entities/#{model.entity_id}/fields/"

        # fallback to opts
        expect Field.$get_api_url opts
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{opts.import_handler_id}/entities/#{opts.entity_id}/fields/"

        # throw
        expect ->
          Field.$get_api_url {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Field.$get_api_url {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Field.$get_api_url {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should have $beforeLoadAll to work with opts or throw exception', inject (Field)->

        expect ->
          Field.$beforeLoadAll {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Field.$beforeLoadAll {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Field.$beforeLoadAll {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"


  describe 'Sqoop Model', ->

    it 'should have Field properties and methods defined', inject (Sqoop)->

      expect(Sqoop.LIST_MODEL_NAME).toEqual 'sqoop_imports'
      expect(Sqoop.MAIN_FIELDS).toEqual 'id,text,target,table,where,direct,mappers,datasource,datasource_id,entity_id'

    it 'can create an instance with predefined properties set', inject (Sqoop)->
      sqoop = new Sqoop
      expect(sqoop.BASE_API_URL).toEqual "#{settings.apiUrl}xml_import_handlers/sqoop_imports/"
      expect(sqoop.API_FIELDNAME).toEqual 'sqoop_import'
      expect(sqoop.LIST_MODEL_NAME).toEqual 'sqoop_imports'
      expect(sqoop.id).toBe null

    it 'constructor filled up', inject (Sqoop)->

      sqoop = new Sqoop {id: 111, text: 'test_sqoop'}

      expect(sqoop.id).toEqual 111
      expect(sqoop.text).toEqual 'test_sqoop'

    describe 'class methods to function properly', ->

      it 'should have $get_api_url to work with model and options', inject (Sqoop)->

        opts = {import_handler_id: 111, entity_id: 333}
        model = {import_handler_id: 222, entity_id: 444}

        # model value take precedence over opts
        expect Sqoop.$get_api_url opts, model
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{model.import_handler_id}/entities/#{model.entity_id}/sqoop_imports/"

        # fallback to opts
        expect Sqoop.$get_api_url opts
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{opts.import_handler_id}/entities/#{opts.entity_id}/sqoop_imports/"

        # throw
        expect ->
          Sqoop.$get_api_url {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Sqoop.$get_api_url {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Sqoop.$get_api_url {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should have $beforeLoadAll to work with opts or throw exception', inject (Sqoop)->

        expect ->
          Sqoop.$beforeLoadAll {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Sqoop.$beforeLoadAll {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Sqoop.$beforeLoadAll {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should call save text and handle errors', inject (Sqoop)->

        sqoop = new Sqoop
        sqoop.saveText()
        expect(sqoop.edit_err).toEqual 'Please enter a text'
        expect(sqoop.loading_state).toBeUndefined()

        sqoop_dict = {id: 999, entity_id: 111, import_handler_id: 222, text: 'some_sqoop_text'}
        sqoop = new Sqoop sqoop_dict
        response = {}
        response[sqoop.API_FIELDNAME] = sqoop_dict
        $httpBackend.expectPUT "#{Sqoop.$get_api_url(sqoop_dict)}#{sqoop.id}/"
        .respond 200, angular.toJson response
        sqoop.saveText()
        $httpBackend.flush()

        expect(sqoop.loading_state).toBe false
        expect(sqoop.msg).toEqual 'Sqoop item has been saved'
        expect(sqoop.edit_err).toBe null
        expect(sqoop.err).toBe null

        # http error
        sqoop_dict = {id: 999, entity_id: 111, import_handler_id: 222, text: 'some_sqoop_text'}
        sqoop = new Sqoop sqoop_dict
        response = {}
        response[sqoop.API_FIELDNAME] = sqoop_dict
        $httpBackend.expectPUT "#{Sqoop.$get_api_url(sqoop_dict)}#{sqoop.id}/"
        .respond 400
        sqoop.saveText()
        $httpBackend.flush()

        expect(sqoop.loading_state).toBe false
        expect(sqoop.msg).toEqual 'http error saving Sqoop item'
        expect(sqoop.edit_err).toBe 'http error saving Sqoop item'
        expect(sqoop.err).toBe 'http save error'


  describe 'XmlQuery Model', ->

    it 'should have Field properties and methods defined', inject (XmlQuery)->

      expect(XmlQuery.MAIN_FIELDS).toEqual 'id,text,target'

    it 'can create an instance with predefined properties set', inject (XmlQuery)->
      xmlQuery = new XmlQuery
      expect(xmlQuery.BASE_API_URL).toEqual "#{settings.apiUrl}xml_import_handlers/queries/"
      expect(xmlQuery.API_FIELDNAME).toEqual 'query'
      expect(xmlQuery.id).toBe null
      expect(xmlQuery.text).toBe null
      expect(xmlQuery.target).toBeUndefined()

    it 'constructor filled up', inject (XmlQuery)->

      xmlQuery = new XmlQuery {}
      expect(xmlQuery.target).toBeUndefined()
      expect(xmlQuery.err).toEqual 'Please enter the query text'

      xmlQuery = new XmlQuery {id: 111, text: 'some text', target: 'some target'}
      expect(xmlQuery.target).toEqual 'some target'
      expect(xmlQuery.text).toEqual 'some text'
      expect(xmlQuery.err).toBeUndefined()

    describe 'class methods to function properly', ->

      it 'should have $get_api_url to work with model and options', inject (XmlQuery)->

        opts = {import_handler_id: 111, entity_id: 333}
        model = {import_handler_id: 222, entity_id: 444}

        # model value take precedence over opts
        expect XmlQuery.$get_api_url opts, model
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{model.import_handler_id}/entities/#{model.entity_id}/queries/"

        # fallback to opts
        expect XmlQuery.$get_api_url opts
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{opts.import_handler_id}/entities/#{opts.entity_id}/queries/"

        # throw
        expect ->
          XmlQuery.$get_api_url {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          XmlQuery.$get_api_url {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          XmlQuery.$get_api_url {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should have $beforeLoadAll to work with opts or throw exception', inject (XmlQuery)->

        expect ->
          XmlQuery.$beforeLoadAll {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          XmlQuery.$beforeLoadAll {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          XmlQuery.$beforeLoadAll {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should call getParamters', inject (XmlQuery)->

        xmlQuery = new XmlQuery {text: 'this is a #{something} query'}
        expect(xmlQuery.getParams()).toEqual ['something']

        xmlQuery = new XmlQuery {text: 'this is a query'}
        expect(xmlQuery.getParams()).toEqual []

      it 'should run sql', inject (XmlQuery)->
        xmlQuery = new XmlQuery {text: 'the text'}
        xmlQuery._runSql = jasmine.createSpy 'xmlQuery._runSql'
        xmlQuery.$run 2, ['something'], 'some_ds', 'handler_url'
        expect(xmlQuery._runSql).toHaveBeenCalledWith 'the text', ['something'],
          'some_ds', 2, 'handler_url/action/run_sql/'


  describe 'Entity Model', ->

    it 'should have Field properties and methods defined', inject (Entity)->

      expect(Entity.LIST_MODEL_NAME).toEqual 'entities'
      expect(Entity.MAIN_FIELDS).toEqual 'id,name'
      expect(Entity.ITEM_NAME).toEqual 'entities'

    it 'can create an instance with predefined properties set', inject (Entity)->
      entity = new Entity
      expect(entity.API_FIELDNAME).toEqual 'entity'
      expect(entity.LIST_MODEL_NAME).toEqual 'entities'
      expect(entity.id).toBe null
      expect(entity.datasource).toBe null
      expect(entity.datasource_id).toBe null
      expect(entity.datasource_name).toBe null
      expect(entity.fields).toEqual []
      expect(entity.import_handler_id).toBe null
      expect(entity.name).toBe null
      expect(entity.query_id).toBe null
      expect(entity.query_obj).toBe null
      expect(entity.entities).toEqual []

    it 'constructor filled up', inject (Entity)->

      entity = new Entity
        id: 111
        import_handler_id: 222
        fields: [{id: 333}, {id: 444}]
        entities: [{id: 555}, {id: 666}]
        query_obj: {id: 777}
        sqoop_imports: [{id: 888}, {id: 999}]

      expect(entity.id).toEqual 111
      expect(entity.import_handler_id).toEqual 222
      expect ({id: x.id} for x in entity.fields)
      .toEqual [{id: 333}, {id: 444}]
      expect ({id: x.id} for x in entity.entities)
      .toEqual [{id: 555}, {id: 666}]
      expect(entity.query_obj.id).toEqual 777
      expect ({id: x.id} for x in entity.sqoop_imports)
      .toEqual [{id: 888}, {id: 999}]



    describe 'class methods to function properly', ->

      it 'should have $get_api_url to work with model and options', inject (Field)->

        opts = {import_handler_id: 111, entity_id: 333}
        model = {import_handler_id: 222, entity_id: 444}

        # model value take precedence over opts
        expect Field.$get_api_url opts, model
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{model.import_handler_id}/entities/#{model.entity_id}/fields/"

        # fallback to opts
        expect Field.$get_api_url opts
        .toEqual "#{settings.apiUrl}xml_import_handlers/#{opts.import_handler_id}/entities/#{opts.entity_id}/fields/"

        # throw
        expect ->
          Field.$get_api_url {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Field.$get_api_url {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Field.$get_api_url {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"

      it 'should have $beforeLoadAll to work with opts or throw exception', inject (Field)->

        expect ->
          Field.$beforeLoadAll {}
        .toThrow new Error "entity_id:undefined, import_handler_id:undefined both should be defined"

        expect ->
          Field.$beforeLoadAll {entity_id: 123}
        .toThrow new Error "entity_id:123, import_handler_id:undefined both should be defined"

        expect ->
          Field.$beforeLoadAll {import_handler_id: 123}
        .toThrow new Error "entity_id:undefined, import_handler_id:123 both should be defined"


  describe 'InputParameter Model', ->

    it 'should have Field properties and methods defined', inject (InputParameter)->

      expect(InputParameter.LIST_MODEL_NAME).toEqual 'input_parameters'
      expect(InputParameter.MAIN_FIELDS).toEqual 'id,name,type,regex,format'
      expect(InputParameter.ITEM_NAME).toEqual 'input_parameters'

    it 'can create an instance with predefined properties set', inject (InputParameter)->
      inputParam = new InputParameter
      expect(inputParam.API_FIELDNAME).toEqual 'xml_input_parameter'
      expect(inputParam.LIST_MODEL_NAME).toEqual 'input_parameters'
      expect(inputParam.id).toBe null
      expect(inputParam.type).toBe null
      expect(inputParam.name).toBe null
      expect(inputParam.regex).toBe null
      expect(inputParam.format).toEqual null


  describe 'Datasource Model', ->

    it 'should have Field properties and methods defined', inject (Datasource)->

      expect(Datasource.LIST_MODEL_NAME).toEqual 'datasources'
      expect(Datasource.MAIN_FIELDS).toEqual 'id,name,type,params'
      expect(Datasource.ITEM_NAME).toEqual 'datasources'

    it 'can create an instance with predefined properties set', inject (Datasource)->
      ds = new Datasource
      expect(ds.API_FIELDNAME).toEqual 'xml_data_source'
      expect(ds.LIST_MODEL_NAME).toEqual 'datasources'
      expect(ds.id).toBe null
      expect(ds.name).toBe null
      expect(ds.type).toBe null
      expect(ds.params).toEqual {}


  describe 'Script Model', ->

    it 'should have Field properties and methods defined', inject (Script)->

      expect(Script.LIST_MODEL_NAME).toEqual 'xml_scripts'
      expect(Script.MAIN_FIELDS).toEqual 'id,import_handler_id,data'
      expect(Script.ITEM_NAME).toEqual 'scripts'

    it 'can create an instance with predefined properties set', inject (Script)->
      script = new Script
      expect(script.API_FIELDNAME).toEqual 'xml_script'
      expect(script.LIST_MODEL_NAME).toEqual 'xml_scripts'
      expect(script.id).toBe null
      expect(script.import_handler_id).toBe null
      expect(script.data).toBe null
