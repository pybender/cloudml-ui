'use strict'

### Controllers ###

angular.module('app.controllers', ['app.config', ])

.controller('AppCtrl', [
  '$scope'
  '$location'
  '$rootScope'

($scope, $location, $rootScope) ->

  # Uses the url to determine if the selected
  # menu item should have the class active.
  $scope.$location = $location
  $scope.pathElements = []
  $scope.$watch('$location.path()', (path) ->
    $scope.activeNavId = path || '/'
  )

  # Breadcrumbs
  $scope.$on('$routeChangeSuccess', ->
    pathElements = $location.path().split('/')
    result = []
    path = ''
    pathElements.shift()

    for _, pathElement of pathElements
      path += '/' + pathElement
      result.push({name: pathElement, path: path})

    $scope.pathElements = result
  )

  # getClass compares the current url with the id.
  # If the current url starts with the id it returns 'active'
  # otherwise it will return '' an empty string. E.g.
  #
  #   # current url = '/products/1'
  #   getClass('/products') # returns 'active'
  #   getClass('/orders') # returns ''
  #
  $scope.getClass = (modelName) ->
    if $scope.activeNavId.substring(0, modelName.length) == modelName
      return 'active'
    else
      return ''

  $rootScope.codeMirrorConfigs = (readOnly, width=500, height=300)->
    json:
      mode: 'application/json'
      readOnly: readOnly
      json: true
      lineWrapping: true
      lineNumbers: true
    python:
      mode: 'text/x-python'
      smartIndent: true
      lineNumbers: true
      matchBrackets: true
      readOnly: readOnly
      onLoad : (cm) ->
        cm.setSize(width, height)
    sql:
      mode: 'text/x-mysql'
      indentWithTabs: true
      smartIndent: true
      lineNumbers: true
      matchBrackets: true
      lineWrapping: true
      readOnly: readOnly
    xml:
      mode: 'application/xml'
      indentWithTabs: true
      smartIndent: true
      lineNumbers: true
      matchBrackets: true
      lineWrapping: true
      readOnly: readOnly
])

.controller('ObjEditCtrl', [
  '$scope'

  ($scope) ->
    $scope.save = (fields) ->
      $scope.model.$save(only: fields).then (() ->
        $scope.editMode = false
      ), ((opts) ->
        $scope.err = $scope.setError(opts, 'saving model')
      )
])

.controller('SaveObjectCtl', [
  '$scope'
  '$location'
  '$timeout'

  ($scope, $location, $timeout) ->
    $scope.init = (model) ->
      $scope.model = model

    $scope.save = (fields) ->
      $scope.saving = true
      $scope.savingProgress = '0%'

      _.defer ->
        $scope.savingProgress = '50%'
        $scope.$apply()

      $scope.model.$save(only: fields).then (->
        $scope.savingProgress = '100%'

        $scope.$emit 'SaveObjectCtl:save:success', $scope.model
        if $scope.LIST_MODEL_NAME?
          LIST_MODEL_NAME = $scope.LIST_MODEL_NAME
        else if $scope.model?.LIST_MODEL_NAME?
          LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME

        if LIST_MODEL_NAME?
          $scope.$emit 'BaseListCtrl:start:load', LIST_MODEL_NAME

        if $scope.model.BASE_UI_URL && !$scope.DONT_REDIRECT
          $location.path $scope.model.objectUrl()
        # timeout the close a little bit late, to make sure listeners have
        # heared the emitted events, or else the transcluded scope of the $modal
        # will be destroyed and no events will be handled. Also SaveObjCtrl some
        # times work outside of a modal, like editing or saving a model and
        # hence there is no modal to close
        if $scope.$close
          $timeout ->
            $scope.$close(true)

      ), ((opts) ->
        $scope.err = $scope.setError(opts, "saving")
        $scope.savingProgress = '0%'
      )

# TODO: nader20140906 never used, see if we can remove it
#    $scope.readFile = (element, name) ->
#      $scope.$apply ($scope) ->
#        $scope.msg = ""
#        $scope.error = ""
#        $scope.data = element.files[0]
#        reader = new FileReader()
#        reader.onload = (e) ->
#          eval("$scope.model." + name + " = e.target.result")
#        reader.readAsText($scope.data)
])

# Controller used for UI Bootstrap pagination
.controller('ObjectListCtrl', [
  '$scope'
  '$q'
  '$timeout'

  ($scope, $q, $timeout) ->
    $scope.pages = 0
    if !$scope.page?
      $scope.page = 1
    $scope.total = 0
    $scope.per_page = 20

    $scope.objects = []
    $scope.loading = false

    $scope.init = (opts={}) ->
      if not _.isFunction(opts.objectLoader)
        throw new Error "Invalid object loader supplied to ObjectListCtrl"

      $scope.objectLoader = opts.objectLoader

      watchLogic = (watchExp, newVal, oldVal) ->
        """
        Since we will be manipulating $watched scope variables, and in case
        of load error we need to reset to the previous. We need to timeout
        on reseting the loading flag, to make sure all $digestion and hence
        watch expression fired wihtout causing the load because of reverting back
        the value (or setting the value from the response). So we use $timeout
        to reset the loading flag
        """
        if newVal isnt oldVal and not $scope.loading
          $scope.loading = true
          $scope.load().then ->
            $timeout ->
              $scope.loading = false
            , 1
          , ->
            $scope[watchExp] = oldVal
            $timeout ->
              $scope.loading = false
            , 1

      $scope.$watch('page', (page, oldVal) ->
        watchLogic 'page', page, oldVal
      , true)

      $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
        watchLogic 'filter_opts', filter_opts, oldVal
      , true)

      # trigger the very first load
      $scope.load()

    $scope.load = ->
      deferred = $q.defer()

      $scope.objectLoader(
        page: $scope.page,
        filter_opts: $scope.filter_opts,
      ).then ((opts) ->
        $scope.total = opts.total
        $scope.page = opts.page || 1
        $scope.pages = opts.pages
        $scope.per_page = opts.per_page
        $scope.objects = opts.objects

        # Notify interested parties by emitting and broadcasting an event
        # Event contains
        $scope.$broadcast 'ObjectListCtrl:load:success', $scope.objects
        deferred.resolve 'page loadded'
      ), ((opts) ->
        $scope.$broadcast 'ObjectListCtrl:load:error', opts
        deferred.reject 'error loading page'
      )

      deferred.promise
])

.controller('BaseDeleteCtrl', [
  '$scope'
  '$location'
  '$timeout'
  '$route'

  ($scope, $location, $timeout, $route) ->
    $scope.resetError()

    $scope.delete = (result) ->
      $scope.model.$delete().then (() ->
        $scope.$emit('modelDeleted', [$scope.model])

        if $scope.LIST_MODEL_NAME?
          LIST_MODEL_NAME = $scope.LIST_MODEL_NAME
        else if $scope.model?.LIST_MODEL_NAME?
          LIST_MODEL_NAME = $scope.model.LIST_MODEL_NAME

        if LIST_MODEL_NAME?
            $scope.$emit 'BaseListCtrl:start:load', LIST_MODEL_NAME
        if $scope.path?
          $location.url $scope.path
          $route.reload()
        # timeout the close a little bit late, to make sure listeners have
        # heared the emitted events, or else the transcluded scope of the $modal
        # will be destroyed and no events will be handled
        $timeout ->
          $scope.$close(true)
        , 100
      ), ((opts) ->
        $scope.setError(opts, $scope.action + ' ' + $scope.model.name)
      )
])

.controller('DialogCtrl', [
  '$scope'
  'openOptions'

  ($scope, openOptions) ->
    $scope.resetError()
    $scope.MESSAGE = openOptions.action
    $scope.model = openOptions.model
    $scope.path = openOptions.path
    $scope.action = openOptions.action
    $scope.LIST_MODEL_NAME = openOptions.list_model_name
])

.controller('BaseListCtrl', [
  '$scope'
  '$rootScope'

  ($scope, $rootScope) ->

    $scope.init = (autoload=true, modelName='noname', autoloadOnFilter=true) ->
      $scope.modelName = modelName
      $scope.autoload = autoload
      $scope.autoloadOnFilter = autoloadOnFilter

      if $scope.autoload
        $scope.load()

      $rootScope.$on(
        'BaseListCtrl:start:load', (event, name, append=false, extra={}) ->
          if name is $scope.modelName
            $scope.load(append, extra)
      )

      if $scope.autoloadOnFilter
        $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
          if filter_opts?
            $scope.load()
        , true)

    $scope.load = (append=false, extra={}) ->
      show = [$scope.FIELDS or []].concat(_.keys($scope.kwargs)).join ','
      params = $.extend({'show': show},
                         $scope.kwargs || {},
                         $scope.filter_opts, extra)
      $scope.MODEL.$loadAll(params).then ((opts) ->
        $scope.pages = opts.pages
        $scope.has_next = opts.has_next
        if append
          $scope.objects = $scope.objects.concat(opts.objects)
        else
          $scope.objects = opts.objects

        $scope.$emit 'BaseListCtrl:load:success', $scope.objects
      ), ((opts) ->
        $scope.setError(opts, $scope.ACTION)
      )

    $scope.loadMore = () ->
      $scope.kwargs['page'] += 1
      $scope.load(true)

    $rootScope.$on('modelChanged', () ->
      $scope.load()
    )

    $scope.sum = (fieldName)->
      return _.reduce $scope.objects, (acc, obj)->
        return acc + obj[fieldName]
      , 0
])