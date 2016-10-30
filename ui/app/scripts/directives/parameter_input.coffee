# Directives for edditing model's, import handler's, transformer's, scaler's parameters

angular.module('app.directives')

.directive('parameterInput', [
  'Model'
  'DataSet'
  'XmlImportHandler'
  'Server'
  'Segment'
  'InputParameter'
  'Cluster'
  'Transformer'
  'TestResult'
  'ModelVerification'
  (Model, DataSet, XmlImportHandler, Server, Segment, InputParameter, Cluster, Transformer, TestResult, ModelVerification) ->
      return {
        require: 'ngModel',
        restrict: 'E',
        scope: {
          config: '='
          value: '=ngModel'
          name: '='
          pdata: '='
        },
        templateUrl:'partials/directives/parameter_input/main.html',
        link: (scope, element, attrs, ngModel) ->
          if !scope.name?
            scope.name = scope.config.name

          scope.loadEntity = () ->
            scope.config.choices = []
            if scope.config.entity == 'Mock'
              mocked = scope.pdata[scope.config.mocked]
              if mocked != undefined
                if typeof(mocked[0]) != "object"
                  for m in mocked
                    scope.config.choices.push {
                      id: m,
                      name: m,
                      type: 'string'
                    }
                else
                  scope.config.choices = mocked
              return

            try
              ent = eval(scope.config.entity)
              to_show = ['id', 'name']
              if scope.config.add_info?
                to_show.push.apply(to_show, scope.config.add_info)
              opts = {
                show: to_show.join(',')
              }

              if scope.config.dependency?
                if scope.pdata? && scope.pdata != undefined && scope.pdata[scope.config.dependency]
                  _.extend opts, scope.pdata
                else
                  throw "Model not ready"

              ent.$loadAll opts
              .then ((opts) ->
                scope.config.choices = opts.objects
                if scope.pdata[scope.name]
                  scope.setAdditionalInfo(scope.pdata[scope.name])
              ), ((opts) ->
                throw "Dependent model "+scope.config.name+" loading error"
              )
            catch e
              console.log e

          if scope.config.entity?
            scope.loadEntity()

          scope.$watch('pdata', (oV, nV, scope) ->
            if nV && nV != oV
              console.log scope.pdata
              if scope.config.dependency? && nV[scope.config.dependency] != oV[scope.config.dependency]
                scope.loadEntity()
          , true)

          scope.setAdditionalInfo = (value) ->
            scope.pdata['import_handler_type'] = 'xml'
            if scope.config.add_info?
              for ai in scope.config.add_info
                if scope.config.choices && scope.config.choices[0][ai]
                  for c in scope.config.choices
                    if parseInt(value) == parseInt(c.id)
                      if ai == 'train_import_handler_id' || ai == 'test_import_handler_id'
                        scope.pdata['import_handler_id'] = c[ai]
                      else
                        scope.pdata[ai] = c[ai]
                      break

          scope.entitySelectHandler = (value) ->
            scope.setAdditionalInfo(value)

          scope.select2Opts = null
          if scope.config.choices
            scope.select2Opts = scope.$root.getSelect2Params(
              {choices: scope.config.choices})

          if scope.config.choose_multiple
            scope.select2Opts = {
              allowClear: true,
              placeholder: 'Please select several '+scope.name,
              width: 230,
              choices: scope.config.choices
            }

          scope.getFieldTemplate = (config) ->
            if config.choices
              if config.type == 'int_float_string_none'
                name = 'int_float_string_none_choices'
              else
                name = 'choices'
              if config.entity
                name = 'entity_choices'
                if config.choose_multiple
                  name = 'entity_choices_multiple'
                if config.dict_fields
                  name = 'recursive_parameter_input'
            else
              if config.name == 'password'
                name = 'password'
              else
                name = config.type

            return "partials/directives/parameter_input/#{name}_field.html"
      }
])

.directive('piStringListNone', () ->
  return {
    require: 'ngModel',
    restrict: 'E',
    scope: {
      config: '='
      value: '=ngModel'
      name: '='
    }
    templateUrl:'partials/directives/parameter_input/string_list_none.html',

    link: (scope, element, attrs, ngModel) ->
      scope.parameterTypes = ['string', 'list', 'empty']
      typeIsArray = Array.isArray || ( value ) -> return {}.toString.call( value ) is '[object Array]'

      typeFor = (val) ->
        res = 'empty'
        if val?
          if typeof val is 'string' then res = 'string'
          if typeIsArray val then res = 'list'
        return res

      displayFor = (val, paramType) ->
        res = val
        if paramType == 'empty' then res = null
        if val? && paramType == 'string' then res = "#{val}"
        if val? && paramType == 'list'
          if typeIsArray val
            res = val.join()
          else
            res = "#{val}"
        return res

      valueFor = (disp, paramType) ->
        if paramType == 'list'
          value = disp.split(',')
        if paramType == 'string'
          value = "#{disp}"
        if paramType == 'empty'
          value = null
        return {
          type: paramType,
          value: value
        }

      scope.parameterType = typeFor(scope.value)
      scope.displayValue = displayFor(scope.value, scope.parameterType)

      scope.change = () ->
      	scope.value = valueFor(scope.displayValue, scope.parameterType)
  }
)