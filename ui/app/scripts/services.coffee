'use strict'

### Sevices ###

services = angular.module('app.services', ['app.config',])

services.factory 'version', -> "2016-08-08"

services.factory('auth', ['$http'
  '$cookieStore'
  '$rootScope'
  'settings'
  ($http, $cookieStore, $rootScope, settings) ->

    $rootScope.user = undefined

    _get_auth_token = () ->
      return $cookieStore.get('auth-token')

    _put_auth_token = (token) ->
      if not token
        $cookieStore.remove('auth-token')
      else
        $cookieStore.put('auth-token', token)

    return {
      get_auth_token: () ->
        return _get_auth_token()

      is_authenticated: () ->
        return not not _get_auth_token()

      login: () ->
        console.log "login"
        console.log Date.now()
        url = settings.apiUrl + "auth/get_auth_url"
        $http(
          method: 'POST'
          headers: settings.apiRequestDefaultHeaders
          url: url
          transformRequest: angular.identity
          params: {}
        ).then ((resp) ->
          console.log "login resp"
          console.log Date.now()
          resp
        )

      authorize: (oauth_token, oauth_verifier) ->
        url = settings.apiUrl + "auth/authenticate"
        console.log "authenticate"
        console.log Date.now()
        console.log url
        console.log angular.identity
        $http(
          method: 'POST'
          headers: settings.apiRequestDefaultHeaders
          url: url
          transformRequest: angular.identity
          params: {
            oauth_token: oauth_token,
            oauth_verifier: oauth_verifier
          }
        ).then ((resp) ->
          token = resp.data.auth_token
          console.log token
          console.log Date.now()
          _put_auth_token(token)
          console.log Date.now()

          resp
        )

      logout: () ->
        _put_auth_token(undefined)
        $rootScope.user = undefined

      get_user: () ->
        if not _get_auth_token()
          return null
        console.log "get user"
        console.log Date.now()
        url = settings.apiUrl + "auth/get_user"
        token = _get_auth_token()
        console.log "Token"
        console.log Date.now()
        $http(
          method: 'POST'
          headers: {
            'Content-Type': undefined,
            'X-Auth-Token': token
          }
          url: url
          transformRequest: angular.identity
          params: {}
        ).then ((resp) ->
          console.log resp.data.user
          console.log Date.now()
          $rootScope.user = resp.data.user
          resp
        )
    }
])
