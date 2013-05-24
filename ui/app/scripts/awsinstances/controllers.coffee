'use strict'

### AwsInstance specific Controllers ###

angular.module('app.awsinstances.controllers', ['app.config', ])

.controller('AwsInstanceListCtrl', [
  '$scope'
  '$http'
  '$dialog'
  'settings'
  'AwsInstance'

($scope, $http, $dialog, settings, AwsInstance) ->
  AwsInstance.$loadAll(
    show: 'name,type,created_on,updated_on,ip'
  ).then ((opts) ->
    $scope.objects = opts.objects
  ), ((opts) ->
    $scope.setError(opts, 'loading aws instances')
  )
])

.controller('AwsInstanceDetailsCtrl', [
  '$scope'
  '$routeParams'
  'AwsInstance'

($scope, $routeParams, AwsInstance) ->
  if not $routeParams.id then err = "Can't initialize without instance id"
  $scope.instance = new AwsInstance({_id: $routeParams.id})

  $scope.instance.$load(
    show: 'name,type,created_on,updated_on,ip,description'
    ).then (->), (-> $scope.setError(opts, 'loading aws instance'))
])

.controller('AddAwsInstanceCtl', [
  '$scope'
  '$http'
  '$location'
  'settings'
  'AwsInstance'

($scope, $http, $location, settings, AwsInstance) ->
  $scope.instance = new AwsInstance()
  $scope.types = [{name: 'small'}, {name: 'large'}]
  $scope.err = ''
  $scope.new = true

  $scope.add = ->
    $scope.saving = true
    $scope.savingProgress = '0%'
    $scope.savingError = null

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.instance.$save().then (->
      $scope.savingProgress = '100%'

      _.delay (->
        $location.path $scope.instance.objectUrl()
        $scope.$apply()
      ), 300

    ), ((resp) ->
      $scope.saving = false
      $scope.setError(opts, 'adding aws instance')
    )
])