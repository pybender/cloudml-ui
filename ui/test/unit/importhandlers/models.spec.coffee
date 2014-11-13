'use strict'

describe "app.importhandlers.model", ->

  beforeEach(module "ngCookies")
  beforeEach(module "ui.bootstrap")

  beforeEach(module "app.base")
  beforeEach(module "app.config")
  beforeEach(module "app.services")

  beforeEach(module "app.importhandlers.model")
  beforeEach(module "app.xml_importhandlers.models")

  describe "BaseQueryModel", ->

    it "should properly parse parameters of %(something)s format",
      inject( (BaseQueryModel) ->
        queryText = """
        SELECT * FROM some_table
        WHERE qi.file_provenance_date >= '%(start)s' AND
        qi.file_provenance_date >= '%(start)s' AND
        qi.file_provenance_date < '%(end)s'
        """
        query = new BaseQueryModel()
        params = query._getParams BaseQueryModel.PARAMS_PERCENT_REGEX, queryText
        expect(params).toEqual ['start', 'end']
      )

    it "should properly parse parameters of \#{something} format",
      inject( (BaseQueryModel) ->
        queryText = """
        SELECT * FROM some_table
        WHERE qi.file_provenance_date >= '\#{start}' AND
        qi.file_provenance_date >= '\#{start}' AND
        qi.file_provenance_date < '\#{end}'
        """
        query = new BaseQueryModel()
        params = query._getParams BaseQueryModel.PARAMS_HASH_REGEX, queryText
        expect(params).toEqual ['start', 'end']
      )

    it "should call $makerequest with coorrect parameters",
      inject( (BaseQueryModel)->
        query = new BaseQueryModel()
        query.$make_request = jasmine.createSpy('$make_request')
        sql = 'somesql'
        limit = 2
        handlerUrl = 'somehandlerurl'
        params = ['start', 'end']
        ds_name = 'ds_name'
        data =
          sql: sql,
          params: JSON.stringify(params),
          limit: limit,
          datasource: ds_name
        query._runSql sql, params, ds_name, limit, handlerUrl
        expect(query.$make_request).toHaveBeenCalledWith handlerUrl, {}, "PUT", data
      )

  describe "Query", ->

    it "should properly parse parameters",
      inject( (Query)->
        queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s'"
        query = new Query({sql: queryText})
        expect(query).toBeDefined()
        expect(query.sql).toEqual queryText
        params = query.getParams()
        expect(params).toEqual ['start', 'end']

        url = "someurl/"
        data =
          sql: queryText
          params: JSON.stringify(params)
          limit: 2
          datasource: 'ds_name'
        query.$make_request = jasmine.createSpy()
        query.$run 2, ['start', 'end'], 'ds_name', url
        expect(query.$make_request).toHaveBeenCalledWith url + "action/run_sql/", {}, "PUT", data
      )

  describe "XmlQuery", ->

    it "should properly parse parameters",
      inject( (XmlQuery)->
        queryText = "SELECT * FROM some_table WHERE qi.file_provenance_date >= '\#\{start\}' AND qi.file_provenance_date < '\#\{end\}'"
        query = new XmlQuery({text: queryText})
        expect(query).toBeDefined()
        expect(query.text).toEqual queryText
        params = query.getParams()
        expect(params).toEqual ['start', 'end']

        url = "someurl"
        data =
          sql: queryText
          params: JSON.stringify(params)
          limit: 2
          datasource: 'ds_name'
        query.$make_request = jasmine.createSpy()
        query.$run 2, ['start', 'end'], 'ds_name', url
        expect(query.$make_request).toHaveBeenCalledWith url + "/action/run_sql/", {}, "PUT", data
      )
