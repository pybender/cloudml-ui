angular.module('app.clusters.models', ['app.config'])

.factory('Cluster', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Cluster  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}instances/clusters/"
      BASE_UI_URL: '/aws/clusters/'
      API_FIELDNAME: 'cluster'

      $createSshTunnel: (opts={}) =>
        @$make_request(
          "#{@BASE_API_URL}#{@id}/action/create_tunnel/", {}, "PUT", opts)

      $terminateSshTunnel: (opts={}) =>
        @$make_request(
          "#{@BASE_API_URL}#{@id}/action/terminate_tunnel/", {}, "PUT", opts)

    return Cluster
])