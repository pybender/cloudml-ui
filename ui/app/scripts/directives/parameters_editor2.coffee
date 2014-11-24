angular.module('app.directives')

.directive('parametersEditor2', ['$compile', '$window', ($compile, $window) ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/parameters_editor2.html'
    replace: false
#    scope:
#      configuration: '='
    controller: ($scope)->
      $scope.fields = {}

      $scope.$watch 'parameterType', (newVal, oldVal)->
        $scope.typeHasChanged()

      $scope.$watch 'configuration', (newVal, oldVal)->
        $scope.typeHasChanged()

      ###
      Called every time we need to update the parameters fields listing
      ###
      $scope.typeHasChanged = ()->
        if not $scope.parameterType or not $scope.configuration
          return

        $scope.fields = {}
        pType = $scope.configuration.types[$scope.parameterType]
        builtInFields = _.union(pType.required_params, pType.optional_params,
          pType.default_params)
        for field in builtInFields
          $scope.fields[field] = $scope.configuration.params[field]
        $scope.hasNoFields = _.isEmpty($scope.fields)

      ###
      Checks if the given parameter field is required or not
      ###
      $scope.isRequired = (fieldName) ->
        return fieldName in $scope.configuration.types[$scope.parameterType].required_params


    link: (scope, element, attributes, ngModel) ->
      attributes.$observe 'parameterType', (val)->
        if not val
          return
        scope.parameterType = val

      ngModel.$render = ->
        scope.data = ngModel.$viewValue

      return


      # special case for mapping, if not set they will be undefined
      scope.keyName = scope.$eval(attributes.keyName)
      scope.valueName = scope.$eval(attributes.valueName)
      console.log 'keyName', scope.keyName, 'valueName', scope.valueName

      scope.getType = (key, value) ->
        if scope.isTopLevel() && scope.paramsConfig
          _conf = scope.paramsConfig[key]
          if _conf
            _type = _conf.type
          else
            _type = TYPE_STRING
          return _type or TYPE_STRING
        return TYPE_STRING

      scope.toggleCollapse = () ->
        if (scope.collapsed)
          scope.collapsed = false
          scope.chevron = "icon-chevron-down"
        else
          scope.collapsed = true
          scope.chevron = "icon-chevron-right"

      # TODO: nader20140912, moving a required parameter to a non-required parameter
      # will not update required-params and hence the required parameter is not
      # required anymore. -- how many required in the previous sentence :)
      scope.moveKey = (obj, key, newkey) ->
        obj[newkey] = obj[key]
        delete obj[key]

      scope.deleteKey = (obj, key) ->
        if scope.isRequired(key)
          $window.alert("Can't delete required parameter")
          return
        if(confirm('Delete "'+key+'" ?'))
          delete obj[key]

      scope.addItem = (obj) ->
        # check input for key
        if (scope.keyName == undefined || scope.keyName.length == 0)
          alert("Please fill in a name")
        else if (scope.keyName.indexOf("$") == 0)
          alert("The name may not start with $ (the dollar sign)")
        else if (scope.keyName.indexOf("_") == 0)
          alert("The name may not start with _ (the underscore)")
        else
          if (obj[scope.keyName])
            if(!confirm('Parameter is already set'))
              return

          # add a new item to object
          _val = ""
          if scope.valueName then _val = scope.valueName
          obj[scope.keyName] = _val

          # clean-up
          scope.keyName = ""
          scope.valueName = ""
          scope.showAddKey = false

      scope.isTopLevel = () ->
        #_.indexOf(_(attributes).keys(), 'inner') < 0
        false

      scope.isEmpty = () ->
        scope.isTopLevel() && _.isEmpty(scope.paramsEditorData)

      if scope.isTopLevel()
        scope.type = TYPE_OBJECT

      # Template Generation
      # recursion
      switchTemplate =
        ''

      # display either "plus button" or "key-value inputs"
      addItemTemplate =
          ''

      # start template
      template = '
           '

      ngModel.$formatters.unshift((viewValue) ->
        if _.isObject(viewValue) and scope.paramsConfig
          for key of viewValue
            conf = scope.paramsConfig[key]
            if not conf then continue
            # Covert "chain" parameter to text
            if conf.type == TYPE_TEXT && _.isObject(viewValue[key])
              viewValue[key] = angular.toJson(viewValue[key])
        return viewValue
      )

      render = () ->
        console.log 'scope.paramsEditorData', scope.paramsEditorData
        console.log 'scope.paramsConfig', scope.paramsConfig

#        newElement = angular.element(template)
#        $compile(newElement)(scope)
#        element.html(newElement)
    }
])

.directive('parameterValidator', ['$compile', ($compile) ->
    ###
      Handles validation of an input field for a feature's type parameters
      Requires $scope.field
    ###
    return {
    restrict: 'A'
    require: 'ngModel'
    controller: ['$scope', '$attrs', ($scope, $attrs)->
    ]
    link: (scope, element, attributes, ngModel) ->

      TYPE_STRING = 'str'
      TYPE_OBJECT = 'dict'
      TYPE_TEXT = 'text'
      TYPE_INT = 'int'

      _validateStrParam = (data) ->
        # string validation is any thing, unless the parameter is required
        # in which case required attribute will suffice
        data = if data then data.trim() else ''
        if scope.field.required and data is ''
          return false
        return true

      _validateJsonParam = (data) ->
        data = if data then data.trim() else ''
        if not scope.field.required and data is ''
          return true

        try
          return jQuery.parseJSON(data) isnt null
        catch e
          return false

      _validateInt = (data) ->
        data = if data then (data + '').trim() else ''
        if not scope.field.required and data is ''
          return true
        return not isNaN(parseInt(data))

#      _validateObjectParam = (data) ->
#        # Hack: remove $$hashKey added by angular
#        data = angular.fromJson(angular.toJson(data))
#        if _.isEmpty(data) then return false
#        else
#          for key of data
#            if data[key] == '' then return false
#        return true

      VALIDATORS = {}
      VALIDATORS[TYPE_STRING] = _validateStrParam
      #VALIDATORS[TYPE_OBJECT] = _validateObjectParam
      VALIDATORS[TYPE_TEXT] = _validateJsonParam
      VALIDATORS[TYPE_INT] = _validateInt

      attributes.$set('required', scope.field.required)

      ngModel.$parsers.push ()->
        scope.field.valid = VALIDATORS[scope.field.type](ngModel.$viewValue)
        ngModel.$setValidity('error', scope.field.valid)
        if not scope.field.valid
          return undefined
        else
          return ngModel.$viewValue

      ngModel.$formatters.push (data)->
        scope.field.valid = VALIDATORS[scope.field.type](data)
        ngModel.$setValidity('error', scope.field.valid)
        return data
  }
])

.directive('dynamicName', ['$parse', ($parse)->
  return {
    restrict: 'A'
    priority: 10000
    controller : ['$scope', '$element', '$attrs', ($scope, $element, $attrs)->
      name = $parse($attrs.dynamicName)($scope)
      delete($attrs['dynamicName'])
      $element.removeAttr('dynamic-name')
      $attrs.$set('name', name)
    ]
  }
])