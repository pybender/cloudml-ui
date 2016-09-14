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

    $scope.authenticate = ->
      console.log "Authenticate func"
      $location.path("/auth/authenticate")
])

.controller('AuthCtl', [
  '$scope'
  '$window'
  'auth'

  ($scope, $window, auth) ->
    $scope.is_authenticated = auth.is_authenticated()
    if $scope.is_authenticated
      $scope.status = 'Already logged in'
      return
    $scope.status = 'Getting data. Please wait...'
    console.log 'logging'
    auth.login().then ((resp) ->
      console.log 'got url'
      $scope.status = 'Redirecting to Upwork. Please wait...'
      $window.location.replace resp.data.auth_url
    ), ((resp) ->
      $scope.setError(resp, 'logging in')
    )
])

.controller('AuthCallbackCtl', [
  '$scope'
  '$window'
  '$http'
  '$location'
  '$routeParams'
  'settings'
  'auth'
  'Model'

  ($scope, $window, $http, $location, $routeParams, settings, auth, Model) ->
    $scope.is_authenticated = auth.is_authenticated()
    if $scope.is_authenticated
      $scope.status = 'Already logged in'
      model = new Model
      $location.url model.BASE_UI_URL
      return
    $scope.status = 'Authorization. Please wait...'
    oauth_token = $location.search().oauth_token
    oauth_verifier = $location.search().oauth_verifier
    console.log "Aith authorize"
    console.log Date.now()
    auth.authorize(oauth_token, oauth_verifier).then ((resp) ->
      $scope.status = 'Authorized'
      console.log 'authorized'
      console.log Date.now()
      $window.location.reload()
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
    $scope.init = ->
      console.log "user ctrl"
      user = auth.get_user()
      console.log Date.now()
      console.log user
      if user
        user.then ((resp) ->
          $scope.user = resp.data.user
          resp
        )

    $scope.logout = ->
      auth.logout()
      location.reload()
])
