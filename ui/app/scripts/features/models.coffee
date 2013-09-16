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
      params: null
      created_on: null
      created_by: null

    return Classifier
])

.factory('FeaturesSet', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class FeaturesSet extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/sets/"
      BASE_UI_URL: "/features/sets/"
      API_FIELDNAME: 'set'
      @MAIN_FIELDS: 'name,schema_name,classifier,
features_count,created_on,created_by'

      _id: null
      name: null
      schema_name: null
      features_count: 0
      classifier: null
      target_variable: null
      created_on: null
      created_by: null

    return FeaturesSet
])

.factory('Feature', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'NamedFeatureType'
  
  ($http, $q, settings, BaseModel, NamedFeatureType) ->
    class Feature extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/items/"
      API_FIELDNAME: 'feature'
      @MAIN_FIELDS: 'name,type,input_format,transformer__name,params,
scaler,default,is_target_variable,created_on,created_by'

      _id: null
      name: null
      type: 'int'
      transformer: null
      input_format: null
      params: {}
      scaler: null
      default: null
      is_required: false
      is_target_variable: false

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