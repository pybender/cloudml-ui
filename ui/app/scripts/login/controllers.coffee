'use strict'

angular.module('app.login.controllers', ['app.config', 'app.services'])

.controller('LoginCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, auth) ->
    $scope.is_authenticated = auth.is_authenticated()
    $scope.loading_state = false

    $scope.authenticate = () =>
      $location.path("/auth/authenticate")
])

.controller('AuthCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, auth) ->
    $scope.is_authenticated = auth.is_authenticated()
    if $scope.is_authenticated
      $scope.status = 'Already logged in'
      return
    $scope.status = 'Getting data. Please wait...'
    auth.login().then ((resp) ->
      $scope.status = 'Redirecting to oDesk. Please wait...'
      window.location.replace(resp.data.auth_url)
    ), ((resp) ->
      $scope.setError(resp, 'logging in')
    )
])

.controller('AuthCallbackCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, auth) ->
    $scope.is_authenticated = auth.is_authenticated()
    if $scope.is_authenticated
      $scope.status = 'Already logged in'
      return
    $scope.status = 'Authorization. Please wait...'
    oauth_token = $location.search().oauth_token
    oauth_verifier = $location.search().oauth_verifier
    auth.authorize(oauth_token, oauth_verifier).then ((resp) ->
      $scope.status = 'Authorized'
      window.location.reload()
    ), ((resp) ->
      $scope.setError(resp, 'authorizing')
    )
])

.controller('UserCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, auth) ->
    $scope.init = () =>
      user = auth.get_user()
      if user
        user.then ((resp) ->
          $scope.user = resp.data.user
          resp
        )

    $scope.logout = () =>
      auth.logout()
      location.reload()
])
