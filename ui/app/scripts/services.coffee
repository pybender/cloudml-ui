'use strict'

### Sevices ###

services = angular.module('app.services', [])

services.factory 'version', -> "0.1"

services.factory('auth', ($http, $cookieStore, $rootScope, settings) ->
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
      url = settings.apiUrl + "auth/get_auth_url"
      $http(
        method: 'POST'
        headers: settings.apiRequestDefaultHeaders
        url: url
        transformRequest: angular.identity
        params: {}
      ).then ((resp) =>
        console.log(resp.data.auth_url)
        resp
      )

    authorize: (oauth_token, oauth_verifier) ->
      url = settings.apiUrl + "auth/authenticate"
      $http(
        method: 'POST'
        headers: settings.apiRequestDefaultHeaders
        url: url
        transformRequest: angular.identity
        params: {
          oauth_token: oauth_token,
          oauth_verifier: oauth_verifier
        }
      ).then ((resp) =>
        console.log(resp.data)
        token = resp.data.auth_token
        _put_auth_token(token)

        resp
      )

    logout: () ->
      _put_auth_token(undefined)
      $rootScope.user = undefined

    get_user: () ->
      if not _get_auth_token()
        return null

      url = settings.apiUrl + "auth/get_user"
      token = _get_auth_token()
      $http(
        method: 'POST'
        headers: {
          'Content-Type': undefined,
          'X-Requested-With': null,
          'X-Auth-Token': token
        }
        url: url
        transformRequest: angular.identity
        params: {}
      ).then ((resp) =>
        $rootScope.user = resp.data.user
        resp
      )
  }
)
