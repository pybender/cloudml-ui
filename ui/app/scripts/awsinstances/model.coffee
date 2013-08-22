angular.module('app.awsinstances.model', ['app.config'])

.factory('AwsInstance', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Aws Instance
    ###
    class AwsInstance  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}aws_instances/"
      BASE_UI_URL: '/aws/instances/'
      API_FIELDNAME: 'instance'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'type', 'ip',
                               'description', 'is_default']

      _id: null
      created_on: null
      updated_on: null
      name: null
      type: null
      description: null
      is_default: null
      ip: null

      loadFromJSON: (origData) =>
        super origData

      $save: (opts={}) =>
        @type = @type['name']
        super opts

    return AwsInstance
])