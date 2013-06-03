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
          scope.obj[fieldName] = obj[fieldName]

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
          editableOpts.source = eval("scope.source")

        $(el).editable editableOpts

        scope.$watch scope.value, (newVal, oldVal) ->
          previousValue = newVal
          $(el).editable 'setValue', newVal
          if attrs.display then $(el).text eval("scope.display")

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
      return () ->
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
