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

.directive('cmlHasCodemirror', [
  '$timeout'

  ($timeout)->
    ###
      Apply it to an element subject to be shown or hidden and has a ui-codemirror
      element that needs to be refreshed accordingly.

      Jira#MATCH-1990
      http://stackoverflow.com/questions/17086538/codemirror-content-not-visible-in-bootstrap-modal-until-it-is-clicked

      Posted an issue regarding it and possible solution
      https://github.com/angular-ui/ui-codemirror/issues/68

      usage:
        <div ng-show="action[1] == 'json'" cml-has-codemirror="action[1] == 'json'">
          <textarea name="data" ui-codemirror="codeMirrorConfigs(true)['json']" ng-model="handler.data_json"></textarea>
        </div>
    ###

    restrict: 'A'
    link: (scope, element, attrs)->
      attrs.$observe 'cmlRefreshCm', (value) ->
        #console.log 'to watch', value
        scope.$watch attrs.cmlHasCodemirror, (newVal)->
          #console.log 'cmlHasCodemirror has new value', newVal
          if newVal
              for cmElem in $('.CodeMirror', element)
                $timeout ->
                  #console.log 'refreshing codemirror element', cmElem
                  cmElem.CodeMirror.refresh()
                , 700
])

.directive('cmlCodemirrorRefresh', [
  '$timeout'

  ($timeout) ->
    ###
      Apply it to ui-codemirror that is not refreshed using ui-refresh of
      ui-codemirror, don't ask me why it is not refreshing :/

      Jira#MATCH-1990
      http://stackoverflow.com/questions/17086538/codemirror-content-not-visible-in-bootstrap-modal-until-it-is-clicked

      Posted an issue regarding it and possible solution
      https://github.com/angular-ui/ui-codemirror/issues/68

      @usage: <textarea ui-codemirror="codeMirrorConfigs(true)['json']" ng-model="dataset.samples_json" class="cml-codemirror-refresh"></textarea>
    ###
    restrict: 'C'
    require: 'ngModel'
    link: (scope, element, attrs)->
      attrs.$observe 'ngModel', (value) ->
        #console.log 'to watch', value
        scope.$watch value, (newValue)->
          #console.log 'for ', value, 'got new value', newValue
          $timeout ->
            #console.log 'refreshing codemirror element', element.next()
            element.next()[0].CodeMirror.refresh()
          , 100
])

# TODO: nader20140909 not used anywhere, schedule for removal
#.directive('showtab', () ->
#  return {
#    link: (scope, element, attrs) ->
#      element.click((e) ->
#        e.preventDefault()
#        $(element).tab('show')
#      )
#  }
#)

# TODO: nader20140909 not used anywhere, schedule for removal
#.directive("fileDownload", [
#  '$compile'
#
#($compile) ->
#  return {
#    restrict: "E"
#    #templateUrl: 'partials/directives/file_downloader.html',
#    scope:{
#      data:'=data'
#      filename: '=filename'
#      text: '=text'
#      cssClass: '=cssClass'}
#    link: (scope, elm, attrs) ->
#      scope.$watch 'data', (val, oldVal) ->
#        if val?
#          blob = new Blob([val], {type: "application/json"})
#          url = URL.createObjectURL(blob)
#          elm.append($compile(
#            '<a class="btn btn-info" download="' + scope.filename + '"' +
#            'href="' + url + '">' + scope.text + '</a>'
#          )(scope))
#  }
#])

# .directive('fileDownload',
#   '$compile'
#   ($compile) ->
#     return {
#       # restrict:'E',
#       # scope:{ getUrlData:'&getData'}
#       # # link: (scope, elm, attrs) ->
#       # #   url = URL.createObjectURL(scope.getUrlData())
#       # #   elm.append($compile(
#       # #     '<a class="btn" download="data.json" href="' +
#       # #     url + '">download</a>'
#       # #   )(scope))
#     }
# )

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
        previousDisplay = null

        successHandler = (obj) ->
          previousValue = obj[fieldName]
          # Update value on given object with value returned with response
          # debugger
          # scope.obj[fieldName] = obj[fieldName]
          # scope.value = obj[fieldName]

        errorHandler = ->
          # Revert changed value
          # TODO: nader20140910 the following line will break the select
          # type. the value is instance.object.id, the field is instance.object
          # assigning the id of the object to instance.object will break it
          scope.obj[fieldName] = previousValue
          $(el).editable 'setValue', previousValue
          #if attrs.display then $(el).text scope.display

        promiseHandler = (promise) ->
          promise.then successHandler, errorHandler

        validateRequired = (value) ->
           $(".editable-error-block").css("font-size", "14px")
           $(".editable-error-block").css("font-weight", "normal")
           if $.trim(value) == ''
             return 'This field is required'

        editableOpts = {
          url: submitFn
          type: inputType
          placement: placement
          autotext: 'never'
          success: promiseHandler
        }

        if inputType == 'select'
          editableOpts.source = scope.source

        if attrs.editableRequired? && scope.$eval(attrs.editableRequired) != false
          editableOpts.validate = validateRequired

        $(el).editable editableOpts

        scope.$watch scope.value, (newVal, oldVal) ->
          if not newVal
            # and edge condition happens with select types when there is a failure
            # in the save request, we protect both prevoiusValue and the input
            return
          previousValue = oldVal
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
    scope: { weights: '=',  options: '=' }
  }
)


.directive('goToDocs', () ->
  return {
    restrict: 'E',
    templateUrl: 'partials/directives/go_to_docs.html',
    replace: true,
    transclude : true,
    link: (scope, el, attrs) ->
      scope.url = "http://cloudml.int.odesk.com/docs/" + \
      attrs.page + ".html#" + (attrs.section || '')
      scope.title = attrs.title || 'click and read the docs for more info'
  }
)

.directive('weightedDataParameters', () ->
  return {
    restrict: 'E',
    templateUrl: 'partials/directives/weighted_data_params.html',
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
    scope: {tree: '=', innerLoad: '&customClick', options: '='}
    # replace: true
    #restrict: 'E'
    transclude : true
    templateUrl:'partials/directives/weights_tree.html'
    compile: () ->
      return () -> undefined
  }
])


.directive("entitiesTree", [ ->
  return {
    scope: {
      handler: '=',
      entity: '=',
      addEntity: '&addEntity',
      addField: '&addField',
      deleteEntity: '&deleteEntity',
      deleteField: '&deleteField',
      editDataSource: '&editDataSource',
      saveQueryText: '&saveQueryText',
      runQuery: '&runQuery',
      addSqoop: '&addSqoop',
      getPigFields: '&getPigFields',
      deleteSqoop: '&deleteSqoop',
    }
    # replace: true
    restrict: 'E'
    transclude : true
    templateUrl:'partials/directives/import_tree.html'

    link: (scope, el, attrs) ->
      scope.getDatasources = (ds_type) ->
        options = []
        for ds in scope.handler.xml_data_sources
          if ds_type and ds.type != ds_type
            continue
          options.push({
            value: ds.id,
            text: ds.name
          })
        return options
  }
])

.directive("entitiesRecursive", [
  '$compile'

($compile) ->
  return {
    restrict: "EACM"
    priority: 100000
    compile: (tElement, tAttr) ->
      contents = tElement.contents().remove()
      compiledContents = undefined
      return (scope, iElement, iAttr) ->
        if not compiledContents
          compiledContents = $compile(contents)
        iElement.append(
          compiledContents(scope, (clone) -> return clone))
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
        #console.log scope.key, scope.val, typeof(scope.val)
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
        if attrs.cmlProgress
          tmpl = '''
            <div class="progress progress-striped active">
              <div class="bar" style="width: 100%;"></div>
            </div>
            '''
          el.addClass('loading-indicator-progress').append $(tmpl)

          el.find('.bar').css width: '0%'
          # Progress attribute value is expected to be a valid watchExpression
          # because it is going to be watched for changes
          scope.$watch attrs.cmlProgress, (newVal, oldVal, scope) ->
            el.find('.bar').css width: newVal
            return 0

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
             msg="savingError" trace="trace" unsafe></alert>

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
          <div>
            <span class="message"></span>&nbsp;
            <a ng-init="show=false" ng-click="show=!show" class="view-trace"></a>
            <span ng-show="show" class="traceback"></span>
          </div>
        </div>
        '''

      link: (scope, el, attrs) ->

        _meth = if attrs.unsafe? then 'text' else 'html'

        el.find('.message')[_meth] ''
        attrs.$observe 'msg', (newVal, oldVal, scope) ->
          if newVal
            el.find('.message')[_meth] newVal

        attrs.$observe 'trace', (newVal, oldVal, scope) ->
          if newVal
            el.find('.view-trace')['html'] '[Error Backtrace]'
            values = newVal.split('\n')
            el.find('.traceback')['html'] values.join('<br/>')

        oldHtmlClass = null
        attrs.$observe 'htmlclass', (newVal, oldVal, scope) ->
          alert = el

          if oldHtmlClass
            alert.removeClass oldHtmlClass

          if newVal
            alert.addClass newVal
            oldHtmlClass = newVal
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

          jsonObj = null
          # jQuery.parseJson('') will return null
          try
            jsonObj = jQuery.parseJSON(viewValue)
          catch e
            isValid = false

          control.$setValidity('jsonFile', isValid and jsonObj isnt null)
          control.$render()
        )
        return viewValue
      )

      element.change((e) ->
        changeEvt = e
        if not changeEvt.target.files or not changeEvt.target.files.length
          control.$setViewValue('')
          control.$render()
          return

        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)
            control.$render()

          reader.readAsText(changeEvt.target.files[0])
        )
      )
  }
)

.directive('xmlFile', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->

      control.$parsers.unshift((viewValue) ->
        scope.$apply( () ->
          isValid = true

          # Validate xml
          try
            xmlDoc = $.parseXML(viewValue)
          catch e
            isValid = false

          control.$setValidity('xmlFile', isValid and xmlDoc isnt null)
          control.$setViewValue(viewValue)
          control.$render()
        )
        return viewValue
      )

      element.change((e) ->
        changeEvt = e
        if not changeEvt.target.files or not changeEvt.target.files.length
          control.$setViewValue('')
          control.$render()
          return

        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)
            control.$render()

          reader.readAsText(changeEvt.target.files[0])
        )
      )
  }
)

.directive('notRequiredFile', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->

      control.$parsers.unshift((viewValue) ->
        scope.$apply( () ->
          control.$render()
        )
        return viewValue
      )
      element.change((e) ->
        changeEvt = e
        if not changeEvt.target.files or not changeEvt.target.files.length
          control.$setViewValue('')
          control.$render()
          return

        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)
            control.$render()

          reader.readAsText(changeEvt.target.files[0])
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
          control.$render()
        )
        return viewValue
      )

      element.change((e) ->
        changeEvt = e
        if not changeEvt.target.files or not changeEvt.target.files.length
          control.$setViewValue('')
          control.$render()
          return

        scope.$apply( () ->
          reader = new FileReader()

          reader.onload = (e) ->
            control.$setViewValue(e.target.result)

          reader.readAsText(changeEvt.target.files[0])
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
        if !viewValue
          control.$setValidity('float', true)
          return null

        if FLOAT_REGEXP.test(viewValue)
          control.$setValidity('float', true)
          return viewValue.replace(',', '.')
        else
          control.$setValidity('float', false)
          return undefined
      )
  }
)

.directive('smartInteger', () ->
  return {
    require: 'ngModel',
    restrict: 'A',
    link: (scope, element, attrs, control) ->
      INT_REGEXP = /^\d+$/

      control.$parsers.unshift((viewValue) ->
        if !viewValue
          control.$setValidity('integer', true)
          return null
        if INT_REGEXP.test(viewValue)
          control.$setValidity('integer', true)
          return parseInt(viewValue)
        else
          control.$setValidity('integer', false)
          return undefined
      )
  }
)

# Override the default input to update on blur
.directive('ngModelOnblur', () ->
  return {
    restrict: 'A',
    require: 'ngModel',
    priority: 1000
    link: (scope, element, attributes, ctrl) ->
      if (attributes.type == 'radio' || attributes.type == 'checkbox')
        return
      element.unbind('input').unbind('keydown').unbind('change')
      element.bind 'blur', () ->
        scope.$apply () ->
          ctrl.$setViewValue element.val()
  }
)

# Directives for creating plots
.directive('scCurves', [ '$timeout', ($timeout)->
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
      $timeout ->
        scope.$watch('curvesDict', updateCurves)
  }
])

.directive('scChart', [ '$timeout', ($timeout) ->
  return {
    restrict: 'E',
    scope: { chartDict: '=',
    width: '@width',
    height: '@height'
    },
    link: (scope, element, attrs) ->
      createSVG(scope, element, attrs.width, attrs.height)
      $timeout ->
        scope.$watch('chartDict', updateChart)
  }
])


.directive('ngDictInput', [ ->
  return {
    restrict: 'E',
    require: 'ngModel',
    scope: {
      name: '='
      value: '=ngModel'
    }
    transclude : true
    replace: false
    templateUrl:'partials/directives/ng_dict_input.html'

    link: (scope, element, attrs, ngModel) ->
      scope.displayValue = JSON.stringify(scope.value)

      scope.change = () ->
        if scope.displayValue != 'auto'
          scope.value = JSON.parse(scope.displayValue)
        else
          scope.value = scope.displayValue
  }
])


.directive('ngName', [ ->
  return {
    restrict: 'A',
    require: '?ngModel',
    link: {
      pre: (scope, element, attrs, ctrl) ->
        if ctrl?
          ctrl.$name = scope.$eval(attrs.ngName)
          attrs.$set('name', ctrl.$name)
    }
  }
])


.directive('stopEvent', ->
  restrict: 'A'
  link: (scope, element, attr) ->
    element.bind attr.stopEvent, (e)->
      e.stopPropagation()
)

createSVG = (scope, element, width=400, height=300) ->
  scope.margin = {top: 20, right: 20, bottom: 30, left: 210}
  if not scope.svg?
    scope.svg = d3.select(element[0])
    .append("svg")
    .style {width: "#{width}px", height: "#{height}px"}

updateCurves = (curvesDict, oldVal, scope) ->
  if !curvesDict
    return
  chart = nv.models.lineChart()
  #console.log 'now updating xLabel with', scope.xLabel
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
    return chartDict

  chart = nv.models.pieChart()
  chart.x((d) -> d.label)
  .y((d) -> d.value)
  .showLabels(true)
  .labelType("percent")
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
    if plotName[0] is '$'
      continue
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
