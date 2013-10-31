'use strict'

### Directives ###

# register the module with Angular
angular.module('app.directives', [
  # require the 'app.service' module
  'app.services'
])

.directive('appVersion', [
  'version'

(version) ->

  (scope, elm, attrs) ->
    elm.text(version)
])

.directive('showtab', () ->
  return {
    link: (scope, element, attrs) ->
      element.click((e) ->
        e.preventDefault()
        $(element).tab('show')
      )
  }
)

.directive('editable',

  () ->
    ###
    Integrates editable widget for updating fields without opening separate
    page.

    Attributes used on the element:

      editable: must point to the object being edited. Object must provide
                $save method implementation that supports ``only`` argument.
      ng-bind: must point to the expression that resolves to default value
               for editable element (i.e. value before user edits it).
               Directive watches it for changes, since it could be changed
               from outside.
      field: name of the field of object referenced by ``editable`` that
             will be updated.
      type: input type to be used with editable plug-in. E.g. text or textarea.

    ###
    return {
      restrict: 'A'
      transclude: true
      scope: {
        obj: '=editable'
        value: '&value'
        source: '&'
        display: '&'
      }

      link: (scope, el, attrs) ->
        fieldName = attrs.editableField
        inputType = attrs.editableInput
        placement = attrs.editablePlacement

        submitFn = (params) ->
          if not scope.obj.$save
            throw new Error "Editable: can't handle object without $save method"

          scope.obj[fieldName] = params.value
          return scope.obj.$save only: [fieldName]

        previousValue = null

        successHandler = (obj) ->
          previousValue = obj[fieldName]
          # Update value on given object with value returned with response
          # debugger
          # scope.obj[fieldName] = obj[fieldName]
          # scope.value = obj[fieldName]

        errorHandler = ->
          # Revert changed value
          scope.obj[fieldName] = previousValue
          $(el).editable 'setValue', previousValue
          if attrs.displayValue then $(el).text attrs.displayValue
          #throw new Error "Error saving job information"

        promiseHandler = (promise) ->
          promise.then successHandler, errorHandler

        editableOpts = {
          url: submitFn
          type: inputType
          placement: placement
          autotext: 'never'
          success: promiseHandler
        }

        if inputType == 'select'
          editableOpts.source = scope.source

        $(el).editable editableOpts

        scope.$watch scope.value, (newVal, oldVal) ->
          previousValue = newVal
          $(el).editable 'setValue', newVal
          if attrs.display then $(el).text scope.display

        attrs.$observe 'display', (newVal, oldVal) ->
          if newVal then $(el).text newVal
    }
)

.directive('weightsTable', () ->
  return {
    restrict: 'E',
    templateUrl: 'partials/directives/weights_table.html',
    replace: true,
    transclude : true,
    scope: { weights: '=' }
  }
)


.directive('weightedDataParameters', () ->
  return {
    restrict: 'E',
    template: """<span>
<span ng-show="!val.weights" title="weight={{ val.weight }}"
class="badge {{ val.css_class }}">{{ val.value }}</span>

<div ng-show="val.weights">
  <span  ng-show="val.type == 'List'"
  ng-init="lword=word.toLowerCase()"
  ng-repeat="word in val.value|words">
    <span ng-show="val.weights[lword].weight"
    title="weight={{ val.weights[lword].weight }}"
    class="badge {{ val.weights[lword].css_class }}">{{ word }}</span>
    <span ng-show="!val.weights[lword].weight">{{ word }}</span></span>

  <span ng-show="val.type == 'Dictionary'"
  ng-repeat="(key, dval) in val.weights">
    <span title="weight={{ dval.weight }}"
    class="badge {{ dval.css_class }}">
      {{ key }}={{ dval.value }}</span></span>
</div>
</span>""",
    replace: true,
    transclude : true,
    scope: { val: '=' }
  }
)


.directive('confusionMatrix', () ->
  return {
    restrict: 'E',
    templateUrl: 'partials/directives/confusion_matrix.html',
    scope: { matrix: '=', url: '=' },
    replace: true,
    transclude : true,
  }
)

.directive("recursive", [
  '$compile'

($compile) ->
  return {
    restrict: "EACM"
    priority: 100000
    compile: (tElement, tAttr) ->
      contents = tElement.contents().remove()
      compiledContents = undefined
      return (scope, iElement, iAttr) ->
        if scope.row.full_name
          return
        if not compiledContents
          compiledContents = $compile(contents)
        iElement.append(
          compiledContents(scope, (clone) -> return clone))
  }
])

.directive("tree", [ ->
  return {
    scope: {tree: '=', innerLoad: '&customClick'}
    # replace: true
    #restrict: 'E'
    transclude : true
    templateUrl:'partials/directives/weights_tree.html'
    compile: () ->
      return () -> undefined
  }
])

.directive("paramsEditor", [ ->
  return {
    scope: {params: '='}
    restrict: 'E',
    replace: true,
    transclude : true,
    templateUrl:'partials/directives/params_editor.html'
    compile: () ->
      return () -> undefined
  }
])

.directive("paramsRecursive", [
  '$compile'

($compile) ->
  return {
    restrict: "EACM"
    priority: 100000
    compile: (tElement, tAttr) ->
      contents = tElement.contents().remove()
      compiledContents = undefined
      return (scope, iElement, iAttr) ->
        console.log scope.key, scope.val, typeof(scope.val)
        #if value instanceof Array
        if typeof(scope.val) != 'object'
          return
        if not compiledContents
          compiledContents = $compile(contents)
        iElement.append(
          compiledContents(scope, (clone) -> return clone))
  }
])

.directive('loadindicator',

  () ->

    ###
    Usage::

      <loadindicator title="Loading jobs..." ng-show="!jobs" progress="'90%'">
      </loadindicator>

    Specify `progress` attribute if you want a progress bar. Value could be
    a string (enclosed in single quotes) or a function reference.
    It will be used as watch expression to dynamically update progress.

    If there's no `progress` attribute, then indicator will be simple ajaxy
    spinner.
    ###

    return {
      restrict: 'E'
      replace: true
      transclude: 'element'
      scope: true
      template: '''
        <div class="loading-indicator">
        </div>
        '''

      link: (scope, el, attrs) ->

        # Show progress bar if progress attribute is specified
        if attrs.progress
          tmpl = '''
            <div class="progress progress-striped active">
              <div class="bar" style="width: 100%;"></div>
            </div>
            '''
          el.addClass('loading-indicator-progress').append $(tmpl)

          el.find('.bar').css width: '0%'
          # Progress attribute value is expected to be a valid watchExpression
          # because it is going to be watched for changes
          scope.$watch attrs.progress, (newVal, oldVal, scope) ->
            el.find('.bar').css width: newVal

        # Spinner otherwise
        else
          tmpl = '''
            <img src="/img/ajax-loader.gif">
            '''
          el.addClass 'loading-indicator-spin'
          el.append $(tmpl)
    }
)


.directive('alertMessage',

  () ->
    ###
    Use like this::

      <alert ng-show="savingError"
             alert-class="alert-error"
             msg="savingError" unsafe></alert>

    ``msg`` is an expression, and ``alert-class`` a string.

    ``unsafe`` is boolean, if present then contents retrieved from ``msg``
    are used to set the HTML content of the alert with all the markup.

    Important: NEVER pass user-generated content to ``msg`` with ``unsafe`` on.
    ###
    return {
      restrict: 'E'
      replace: true
      scope: true

      template: '''
        <div class="alert alert-block">
          <button type="button"
            class="close" data-dismiss="alert">&times;</button>
          <div class="message"></div>
        </div>
        '''

      link: (scope, el, attrs) ->

        unsafe = attrs.unsafe
        _meth = if unsafe is undefined then 'text' else 'html'

        el.find('.message')[_meth] ''
        attrs.$observe 'msg', (newVal, oldVal, scope) ->
          if newVal
            el.find('.message')[_meth] newVal

        attrs.$observe 'htmlclass', (newVal, oldVal, scope) ->
          alert = el

          if oldVal
            alert.removeClass oldVal

          if newVal
            alert.addClass newVal
    }
)

# Directives for forms validation

.directive('jsonFile', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->

      control.$parsers.unshift((viewValue) ->
        scope.$apply( () ->
          isValid = true

          try
            jQuery.parseJSON(viewValue)
          catch e
            isValid = false

          control.$setValidity('jsonFile', isValid)
          control.$render()
        )
        return viewValue
      )

      element.change((e) ->
        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)
            control.$render()

          reader.readAsText(element[0].files[0])
        )
      )
  }
)

.directive('requiredFile', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->

      control.$parsers.unshift((viewValue) ->
        scope.$apply( () ->
          control.$setValidity('requiredFile', viewValue != '')
        )
        return viewValue
      )

      element.change((e) ->
        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)

          reader.readAsText(element[0].files[0])
        )
      )
  }
)

.directive('smartFloat', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->
      FLOAT_REGEXP = /^\-?\d+((\.|\,)\d+)?$/

      control.$parsers.unshift((viewValue) ->
        if FLOAT_REGEXP.test(viewValue)
          control.$setValidity('float', true)
          return parseFloat(viewValue.replace(',', '.'))
        else
          control.$setValidity('float', false)
          return undefined
      )
  }
)

# Override the default input to update on blur
.directive('ngModelOnblur', () ->
  return {
    restrict: 'A',
    require: 'ngModel',
    link: (scope, element, attributes, ctrl) ->
      if (attributes.type == 'radio' || attributes.type == 'checkbox')
        return
      element.unbind('input').unbind('keydown').unbind('change')
      element.bind 'blur', () ->
        scope.$apply () ->
          ctrl.$setViewValue element.val()
  }
)

.directive('parametersEditor', ['$compile', ($compile) ->
  return {
    restrict: 'E',
    require: '?ngModel',
    link: (scope, element, attributes, ngModel) ->
      TYPE_STRING = 'str'
      TYPE_OBJECT = 'dict'
      TYPE_TEXT = 'text'

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

      scope.moveKey = (obj, key, newkey) ->
        obj[newkey] = obj[key]
        delete obj[key]

      scope.deleteKey = (obj, key) ->
        if scope.isRequired(key)
          alert("Can't delete required parameter")
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

      scope.isRequired = (key) ->
        if scope.requiredParams && scope.isTopLevel()
          _.indexOf(scope.requiredParams, key) > -1
        else
          false

      scope.isTopLevel = () ->
        _.indexOf(_(attributes).keys(), 'inner') < 0

      scope.isEmpty = () ->
        scope.isTopLevel() && _.isEmpty(scope.paramsEditorData)

      if scope.isTopLevel()
        scope.type = TYPE_OBJECT

      # Template Generation
      # recursion
      switchTemplate =
        '<span ng-switch on="getType(key, paramsEditorData[key])" >
        <div ng-switch-when="dict">
        <parameters-editor ng-model="$parent.paramsEditorData[key]"
          inner="">
        </parameters-editor>
        </div>
        <span ng-switch-when="text" class="jsonLiteral">
          <textarea name="params" ng-model="paramsEditorData[key]"
            class="span5"
            rows="3"
            ng-model-onblur>
          </textarea>
        </span>
        <span ng-switch-default class="jsonLiteral">
          <input type="text" ng-model="paramsEditorData[key]" ng-model-onblur
            placeholder="Empty" />
        </span>
        </span>'

      # display either "plus button" or "key-value inputs"
      addItemTemplate =
        '<div ng-switch on="showAddKey" class="block"
          ng-init="valueType=\'' + TYPE_STRING + '\'">
          <span ng-switch-when="true">
            <input placeholder="Name" type="text"
              class="input-small addItemKeyInput"
              ng-model="$parent.keyName" />
            <span> :
              <input type="text" placeholder="Value"
                class="input-medium addItemValueInput"
                ng-model="$parent.valueName" />
            </span>
            <button class="btn btn-primary"
              ng-click="addItem(paramsEditorData)">
                Add
            </button>
            <button class="btn" ng-click="$parent.showAddKey=false">
              Cancel
            </button>
          </span>
          <span ng-switch-default>
            <button class="addObjectItemBtn"
              ng-click="$parent.showAddKey = true">
              <i class="icon-plus"></i></button>
            </span>
        </div>'

      # start template
      template = '
      <div ng-show="isEmpty()">
        There are no parameters to edit
      </div>
      <div class="jsonContents">
      <span class="block" ng-hide="key.indexOf(\'_\') == 0"
        ng-repeat="(key, value) in paramsEditorData">
        <span class="jsonObjectKey">
          <input ng-disabled="isRequired(key)" class="keyinput"
            type="text"
            ng-model="newkey"
            ng-init="newkey=key"
            ng-change="moveKey(paramsEditorData, key, newkey)"/>
          <i ng-hide="isRequired(key)"
            class="deleteKeyBtn icon-trash"
            ng-click="deleteKey(paramsEditorData, key)">
          </i>
        </span>
        <span class="jsonObjectValue">&nbsp;:&nbsp;
        ' + switchTemplate + '</span>
        <i ng-show="isRequired(key)" class="badge">
          {{ paramsConfig[key].help_text }}
        </i>
        </span><div ng-hide="isTopLevel()">' + addItemTemplate + '</div>
      </div>'

      ngModel.$formatters.unshift((viewValue) ->
        if _.isObject(viewValue)
          for key of viewValue
            conf = scope.paramsConfig[key]
            if not conf then continue
            # Covert "chain" parameter to text
            if conf.type == TYPE_TEXT && _.isObject(viewValue[key])
              viewValue[key] = angular.toJson(viewValue[key])
        return viewValue
      )

      render = () ->
        newElement = angular.element(template)
        $compile(newElement)(scope)
        element.html(newElement)
        if scope.isTopLevel()
          scope.validate()

      ngModel.$render = () ->
        scope.paramsEditorData = ngModel.$viewValue
        render()

      scope.$watch 'paramsConfig', (newValue, oldValue) ->
        render()

      scope.$watch 'requiredParams', (newValue, oldValue) ->
        render()

      _validateStrParam = (key, data) ->
        return data != ''

      _validateObjectParam = (name, data) ->
        # Hack: remove $$hashKey added by angular
        data = angular.fromJson(angular.toJson(data))
        if _.isEmpty(data) then return false
        else
          for key of data
            if data[key] == '' then return false
        return true

      _validateJsonParam = (key, data) ->
        if data == ''
          return false
        try
          jQuery.parseJSON(data)
          return true
        catch e
          return false

      VALIDATORS = {}
      VALIDATORS[TYPE_STRING] = _validateStrParam
      VALIDATORS[TYPE_OBJECT] = _validateObjectParam
      VALIDATORS[TYPE_TEXT] = _validateJsonParam

      scope.validate = () ->
        if !scope.paramsEditorData then return
        errs = []

        for key of scope.paramsEditorData
          data = scope.paramsEditorData[key]
          conf = scope.paramsConfig[key]
          if not conf then return
          validator = VALIDATORS[conf.type]
          if !validator(key, data)
              errs.push key

        ngModel.$setValidity('params', errs.length <= 0)

      if scope.isTopLevel()
        scope.$watch 'paramsEditorData', (newValue, oldValue) ->
          scope.validate()
        , true
  }
])

# Directives for creating plots

.directive('scCurves', [ ->
  return {
    restrict: 'E',
    scope: { curvesDict: '=',
    xLabel:'@xlabel',
    yLabel: '@ylabel',
    showLine: '@showLine',
    width: '@width',
    height: '@height'
    },
    link: (scope, element, attrs) ->
      createSVG(scope, element, attrs.width, attrs.height)
      scope.$watch('curvesDict', updateCurves)
  }
])

.directive('scChart', [ ->
  return {
    restrict: 'E',
    scope: { chartDict: '=',
    width: '@width',
    height: '@height'
    },
    link: (scope, element, attrs) ->
      createSVG(scope, element, attrs.width, attrs.height)
      scope.$watch('chartDict', updateChart)
  }
])

createSVG = (scope, element, width=400, height=300) ->
  scope.margin = {top: 20, right: 20, bottom: 30, left: 210}
  if not scope.svg?
    scope.svg = d3.select(element[0])
    .append("svg")
    .attr("width", width)
    .attr("height", height)

updateCurves = (curvesDict, oldVal, scope) ->
  if !curvesDict
    return
  chart = nv.models.lineChart()
  chart.xAxis.orient('bottom')
    .axisLabel(scope.xLabel)
    .tickFormat(d3.format(',r'))
  chart.yAxis.orient('left')
    .axisLabel(scope.yLabel)
    .tickFormat(d3.format(',.f'))

  scope.svg.datum(getPlotData(curvesDict, scope.showLine))
  .transition().duration(500)
  .call(chart)
  nv.utils.windowResize(chart.update)

updateChart = (chartDict, oldVal, scope) ->
  if !chartDict
    return

  getChartData = (chartDict) ->
    return [{ key: "Probabilities", values: chartDict}]

  chart = nv.models.pieChart()
  chart.x((d) -> d.label)
  .y((d) -> d.value)
  .showLabels(true)
  .labelThreshold(.05)

  scope.svg.datum(getChartData(chartDict))
  .transition().duration(500)
  .call(chart)

  nv.utils.windowResize(chart.update)

zip = () ->
  lengthArray = (arr.length for arr in arguments)
  length = Math.min(lengthArray...)
  for i in [0...length]
    arr[i] for arr in arguments

getPlotData = (curvesDict, addLine) ->
  plots_data = []
  for plotName, plotData of curvesDict
    if plotData? && plotData[0]? && plotData[1]?
      data = zip(plotData[0], plotData[1])
      step = 1 / data.length
      values = ({x: data[i][0], y: data[i][1]} for i in [0...data.length])
      plots_data.push({"values": values, key: plotName})

  if addLine && data?
    line_data = ({x: step*i, y: step*i } for i in [0...data.length])
    plots_data.push({
      values: line_data,
      key: "line"
    })
  return plots_data
