'use strict'

angular.module('app.login.controllers', ['app.config', ])

.controller('LoginCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, $auth) ->
    $scope.is_authenticated = $auth.is_authenticated()
    $scope.loading_state = false

    $scope.authenticate = () =>
      params = "menubar=no,location=no,width=840,height=500"
      url = "/#auth/authenticate"
      $scope.loading_state = true
      w = window.open(url, 'Authentication', params)
      w.focus()
])

.controller('AuthCtl', [
  '$scope'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'

  ($scope, $http, $location, $routeParams, settings, $auth) ->
    $scope.status = 'Getting data. Please wait...'
    $auth.login().then ((resp) ->
      $scope.status = 'Redirecting to oDesk. Please wait...'
      window.location = resp.data.auth_url
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

  ($scope, $http, $location, $routeParams, settings, $auth) ->
    $scope.status = 'Authorization. Please wait...'
    oauth_token = $location.search().oauth_token
    oauth_verifier = $location.search().oauth_verifier
    $auth.authorize(oauth_token, oauth_verifier).then ((resp) ->
      $scope.status = 'Authorized'
      window.opener.location.reload()
      window.close()
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

  ($scope, $http, $location, $routeParams, settings, $auth) ->
    $scope.init = () =>
      user = $auth.get_user()
      if user
        user.then ((resp) ->
          $scope.user = resp.data.user
          resp
        )

    $scope.logout = () =>
      $auth.logout()
      location.reload()
])
