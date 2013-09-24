angular.module('app.features.models', ['app.config'])

.factory('Classifier', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Classifier extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/classifiers/"
      BASE_UI_URL: "/features/classifiers/"
      API_FIELDNAME: 'classifier'
      @MAIN_FIELDS: 'name,type,created_on,created_by,params'
      @$TYPES_LIST: ['stochastic gradient descent classifier',
      'support vector regression', 'logistic regression']

      _id: null
      name: null
      type: null
      params: {}
      created_on: null
      created_by: null

      constructor: (opts) ->
        super opts
        @TYPES_LIST = Classifier.$TYPES_LIST

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@_id}/action/configuration/",
                       load=false)

      $save: (opts={}) =>
        @params = JSON.stringify(@params)
        super opts

    return Classifier
])

.factory('FeaturesSet', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'Classifier'
  
  ($http, $q, settings, BaseModel, Classifier) ->
    class FeaturesSet extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/sets/"
      BASE_UI_URL: "/features/sets/"
      API_FIELDNAME: 'set'
      @MAIN_FIELDS: 'name,schema_name,classifier,
features_count,created_on,created_by,target_variable'

      _id: null
      name: null
      schema_name: null
      features_count: 0
      classifier: null
      target_variable: null
      created_on: null
      created_by: null

      loadFromJSON: (origData) =>
        super origData

        if origData? and origData.classifier?
          @classifier = new Classifier(origData.classifier)

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@_id}/action/download/"

    return FeaturesSet
])

.factory('Feature', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'NamedFeatureType'
  'Transformer'
  
  ($http, $q, settings, BaseModel, NamedFeatureType, Transformer) ->
    class Feature extends BaseModel
      API_FIELDNAME: 'feature'
      @MAIN_FIELDS: 'name,type,input_format,transformer,params,
scaler,default,is_target_variable,created_on,created_by,required'

      _id: null
      name: null
      type: 'int'
      features_set_id: null
      transformer: null
      input_format: null
      params: null
      scaler: null
      default: null
      is_required: false
      is_target_variable: false

      loadFromJSON: (origData) =>
        super origData
        
        if origData?
          if origData.transformer?
            @transformer = new Transformer(origData.transformer)
          if origData.required?
            @required = origData.required == true || origData.required == 'True'

      constructor: (opts) ->
        super opts
        @BASE_API_URL = Feature.$get_api_url(@features_set_id)

      @$get_api_url: (features_set_id) ->
        return "#{settings.apiUrl}features/#{features_set_id}/items/"

      @$loadAll: (opts) ->
        features_set_id = opts.features_set_id
        if not features_set_id
          throw new Error "Feature Set is required"

        extra = {loaded: true, features_set_id: features_set_id}
        resolver = (resp, Model) ->
          {
            objects: (
              new Model(_.extend(obj, extra)) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(Feature.$get_api_url(features_set_id),
                           resolver, opts)

      $save: (opts={}) =>
        super opts

    return Feature
])


.factory('Transformer', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Transformer extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/transformers/"
      BASE_UI_URL: "/features/transformers/"
      API_FIELDNAME: 'transformer'
      @MAIN_FIELDS: 'name,type,params,created_on,created_by'
      @$TYPES_LIST: ['Dictionary', 'Count', 'Tfidf']

      _id: null
      name: null
      type: null
      params: null
      created_on: null
      created_by: null

      $save: (opts={}) =>
        if @params?
          @params = JSON.stringify(@params)
        super opts

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@_id}/action/configuration/",
                       load=false)

    return Transformer
])

.factory('NamedFeatureType', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class NamedFeatureType extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/named_types/"
      BASE_UI_URL: "/features/types/"
      API_FIELDNAME: 'named_type'
      @MAIN_FIELDS: 'name,type,input_format,params,created_on,created_by'
      @$TYPES_LIST: ['boolean', 'int', 'float', 'numeric', 'date',
                   'map', 'categorical_label', 'categorical',
                   'text', 'regex', 'composite']

      _id: null
      name: null
      type: 'int'
      input_format: null
      params: null
      created_on: null
      created_by: null
                   
    return NamedFeatureType
])