# Base models for any import handler type declared in this module

angular.module('app.importhandlers.models', ['app.config'])

.factory('BaseQueryModel', [
  'BaseModel'

  (BaseModel)->
    class BaseQueryModel extends BaseModel
      @PARAMS_PERCENT_REGEX: "%\\((\\w+)\\)s"
      @PARAMS_HASH_REGEX: '#{(\\w+)}'

      _getParams: (exp, sql) ->
        params = []
        regex = new RegExp(exp, 'gi')
        matches = regex.exec(sql)
        while matches
          if matches[1] not in params
            params.push matches[1]
          matches = regex.exec(sql)
        return params

      _runSql: (sql, params, datasource, limit, handlerUrl) ->
        data =
          sql: sql,
          params: JSON.stringify(params),
          limit: limit,
          datasource: datasource
        @$make_request handlerUrl, {}, "PUT", data
  ])