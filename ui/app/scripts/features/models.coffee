angular.module('app.features.models', ['app.config'])

.factory('FeaturesSet', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class FeaturesSet extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}tags/"
      API_FIELDNAME: 'tag'

      _id: null
      id: null
      text: null

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
      BASE_API_URL: "#{settings.apiUrl}tags/"
      API_FIELDNAME: 'tag'

      TRANSFORMER_TYPES: ['Dictionary', 'Count', 'Tfidf']

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
                   
    return NamedFeatureType
])