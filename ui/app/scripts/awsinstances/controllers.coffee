'use strict'

### Instance specific Controllers ###

angular.module('app.awsinstances.controllers', ['app.config', ])

.controller('AwsInstanceListCtrl', [
  '$scope'
  '$rootScope'
  'AwsInstance'

($scope, $rootScope, AwsInstance) ->
  $scope.load = () ->
    AwsInstance.$loadAll(
      show: 'name,type,created_on,updated_on,ip,is_default,created_by,
updated_by'
    ).then ((opts) ->
      $scope.objects = opts.objects
    ), ((opts) ->
      $scope.setError(opts, 'loading instances')
    )

  $scope.load()

  $rootScope.$on('updateList', () ->
    $scope.load()
  )
])

.controller('InstanceActionsCtrl', [
  '$scope'
  'AwsInstance'

($scope, $rootScope, AwsInstance) ->
  $scope.makeDefault = (instance) ->
    instance.is_default = true
    instance.$save().then (->
      $scope.$emit('updateList', [])
    ), ((opts) ->
      $scope.setError(opts, 'updating instance')
      $scope.$emit('updateList', [])
    )
])

.controller('AwsInstanceDetailsCtrl', [
  '$scope'
  '$routeParams'
  'AwsInstance'

($scope, $routeParams, AwsInstance) ->
  if not $routeParams.id then err = "Can't initialize without instance id"
  $scope.instance = new AwsInstance({id: $routeParams.id})

  $scope.instance.$load(
    show: 'name,type,created_on,updated_on,ip,description,is_default,
created_by'
    ).then (->), ((opts)-> $scope.setError(opts, 'loading instance'))
])

.controller('AddAwsInstanceCtl', [
  '$scope'
  '$location'
  'AwsInstance'

  ($scope, $location, AwsInstance) ->
    $scope.model = new AwsInstance()
    $scope.types = [{name: 'small'}, {name: 'large'}]
    $scope.err = ''
    $scope.new = true
])


.controller('GetInstanceCtrl', [
  '$scope'
  'AwsInstance'

  ($scope, AwsInstance) ->
    AwsInstance.$loadAll(
      show: 'name,id,ip,is_default'
    ).then ((opts) ->
      $scope.instances = opts.objects
      if $scope.instances?
        $scope.instances.unshift({
          id: '',
          name: '--- select instance ---'
        })
      for inst in $scope.instances
        if inst.is_default
          $scope.data.aws_instance = inst.id
          break

    ), ((opts) ->
      $scope.err = $scope.setError(opts, 'loading instances')
    )
])


.controller('SpotInstanceRequestCtrl', [
  '$scope'

  ($scope) ->
    # http://aws.amazon.com/amazon-linux-ami/instance-type-matrix/
    $scope.types = ['m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge',
    'hi1.4xlarge', 'hs1.8xlarge']
])
