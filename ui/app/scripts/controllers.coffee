'use strict'

### Controllers ###

angular.module('app.controllers', ['app.config', ])

.controller('AppCtrl', [
  '$scope'
  '$location'
  '$resource'
  '$rootScope'
  'settings'

($scope, $location, $resource, $rootScope, settings) ->

  # Uses the url to determine if the selected
  # menu item should have the class active.
  $scope.$location = $location
  $scope.pathElements = []
  $scope.$watch('$location.path()', (path) ->
    $scope.activeNavId = path || '/'
  )

  # Breadcrumbs
  $scope.$on('$routeChangeSuccess', (event, current) ->
    pathElements = $location.path().split('/')
    result = []
    path = ''
    pathElements.shift()
    pathParamsLookup = {}

    for key, pathElement of pathElements
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
  $scope.getClass = (id) ->
    if $scope.activeNavId.substring(0, id.length) == id
      return 'active'
    else
      return ''
])

.controller('ObjEditCtrl', [
  '$scope'

  ($scope) ->
    $scope.save = (fields) =>
      $scope.model.$save(only: fields).then (() ->
        $scope.editMode = false
      ), ((opts) ->
         $scope.err = $scope.setError(opts, 'saving model')
      )
])

.controller('SaveObjectCtl', [
  '$scope'
  '$location'

  ($scope, $location) ->
    $scope.save = (fields) ->
      $scope.saving = true
      $scope.savingProgress = '0%'

      _.defer ->
        $scope.savingProgress = '50%'
        $scope.$apply()

      $scope.model.$save(only: fields).then (->
        $scope.savingProgress = '100%'

        _.delay (->
          $location.path $scope.model.objectUrl()
          $scope.$apply()
        ), 300

      ), ((opts) ->
        $scope.err = $scope.setError(opts, "saving")
        $scope.savingProgress = '0%'
      )

    $scope.readFile = (element, name) ->
      $scope.$apply ($scope) ->
        $scope.msg = ""
        $scope.error = ""
        $scope.data = element.files[0]
        reader = new FileReader()
        reader.onload = (e) ->
          eval("$scope.model." + name + " = e.target.result")
        reader.readAsText($scope.data)
])

# Controller used for UI Bootstrap pagination
.controller('ObjectListCtrl', [
  '$scope'

  ($scope) ->
    $scope.pages = 0
    if !$scope.page?
      $scope.page = 1
    $scope.total = 0
    $scope.per_page = 20

    $scope.objects = []
    $scope.loading = false

    $scope.init = (opts={}) =>
      if not _.isFunction(opts.objectLoader)
        throw new Error "Invalid object loader supplied to ObjectListCtrl"

      $scope.objectLoader = opts.objectLoader
      $scope.$watch('page', (page, oldVal, scope) ->
        $scope.load()
      , true)

      $scope.$watch('filter_opts ', (filter_opts, oldVal, scope) ->
        $scope.load()
      , true)

    $scope.load = =>
      if $scope.loading
        return false

      $scope.loading = true
      $scope.objectLoader(
        page: $scope.page,
        filter_opts: $scope.filter_opts,
      ).then ((opts) ->
        $scope.loading = false
        $scope.total = opts.total
        $scope.page = opts.page || 1
        $scope.pages = opts.pages
        $scope.per_page = opts.per_page
        $scope.objects = opts.objects

        # Notify interested parties by emitting and broadcasting an event
        # Event contains
        $scope.$broadcast 'ObjectListCtrl:load:success', $scope.objects
      ), ((opts) ->
        $scope.$broadcast 'ObjectListCtrl:load:error', opts
      )
])

.controller('BaseDeleteCtrl', [
  '$scope'
  '$location'

  ($scope, $location) ->
    $scope.resetError()

    $scope.delete = (result) ->
      $scope.model.$delete().then (() ->
        $scope.close()
        $scope.$emit('modelDeleted', [$scope.model])
        $scope.$broadcast('modelDeleted', [$scope.model])
        $location.path $scope.path
      ), ((opts) ->
        $scope.setError(opts, $scope.action + ' ' + $scope.model.name)
      )
])

.controller('DialogCtrl', [
  '$scope'
  '$location'
  'dialog'

  ($scope, $location, dialog) ->
    $scope.resetError()
    $scope.MESSAGE = dialog.action
    $scope.model = dialog.model
    $scope.path = dialog.path
    $scope.action = dialog.action

    $scope.close = ->
      dialog.close()
])

.controller('BaseListCtrl', [
  '$scope'
  '$rootScope'

  ($scope, $rootScope) ->

    $scope.init = (autoload=true, modelName='noname') ->
      $scope.modelName = modelName
      $scope.autoload = autoload

      if $scope.autoload
        $scope.load()
      else
        $rootScope.$on('BaseListCtrl:start:load', (event, name) ->
          if name == $scope.modelName
            $scope.load()
        )

      $scope.$watch('filter_opts ', (filter_opts, oldVal, scope) ->
        $scope.load()
      , true)

    $scope.load = (append=false) ->
      params = $.extend({'show': $scope.FIELDS},
                         $scope.kwargs || {},
                         $scope.filter_opts)

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

    $rootScope.$on('modelDeleted', () ->
      $scope.load()
    )
    $rootScope.$on('modelCreated', () ->
      $scope.load()
    )
])
