isEmpty = (dict) ->
  for prop, val of dict
    if dict.hasOwnProperty(prop) then return false
  true

getVal = (val) ->
  if val? && typeof(val) == 'object'
    if !isEmpty(val)
      val = JSON.stringify(val)
    else
      val = null
  return val


angular.module('app.features.models', ['app.config'])

.factory('Transformer', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Transformer extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/transformers/"
      #BASE_UI_URL: "/features/transformers/"
      API_FIELDNAME: 'transformer'
      @LIST_MODEL_NAME: 'transformers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,params,created_on,created_by'
      @$TYPES_LIST: ['Dictionary', 'Count', 'Tfidf', 'Lda', 'Lsi']

      id: null
      name: null
      type: null
      params: null

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)

      constructor: (opts) ->
        _.extend @, opts
 
    return Transformer
])


.factory('Scaler', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    class Scaler extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/scalers/"
      API_FIELDNAME: 'scaler'
      @LIST_MODEL_NAME: 'scalers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,params,created_on,created_by'
      @$TYPES_LIST: ['MinMaxScaler', 'StandardScaler']

      id: null

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)

      constructor: (opts) ->
        _.extend @, opts
 
    return Scaler
])

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
      @LIST_MODEL_NAME: 'classifiers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,created_on,created_by,params'
      @$TYPES_LIST: ['stochastic gradient descent classifier',
      'support vector regression', 'logistic regression']

      id: null
      name: null
      type: null
      params: {}
      feature_id: null
      created_on: null
      created_by: null

      constructor: (opts) ->
        super opts
        @TYPES_LIST = Classifier.$TYPES_LIST

      loadFromJSON: (origData) ->
        super origData

        # # TODO: quick fix: need better input to edit dict parameter
        # if origData? && origData.params? && origData.params.class_weight
        #   @params['class_weight'] =
        #   JSON.stringify(origData.params.class_weight)

      $getConfiguration: (opts={}) ->
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)

    return Classifier
])

.factory('FeaturesSet', [
  'settings'
  'BaseModel'
  'Feature'
  
  (settings, BaseModel, Feature) ->
    class FeaturesSet extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/sets/"
      BASE_UI_URL: "/features/sets/"
      API_FIELDNAME: 'feature_set'
      @MAIN_FIELDS: 'id,schema_name,features_count,target_variable'

      id: null
      schema_name: null
      features_count: 0
      target_variable: null

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.group_by?
            @group_by = []
            for feature in origData.group_by
              @group_by.push {id: feature.id, text: feature.name}
            console.log @group_by

      downloadUrl: =>
        return "#{@BASE_API_URL}#{@id}/action/download/"

    return FeaturesSet
])

.factory('Feature', [
  'settings'
  '$filter'
  'BaseModel'
  'NamedFeatureType'
  'Transformer'
  'Scaler'
  
  (settings, $filter, BaseModel, NamedFeatureType, Transformer, Scaler) ->
    class Feature extends BaseModel
      API_FIELDNAME: 'feature'
      @MAIN_FIELDS: 'id,name,type,input_format,transformer,params,\
scaler,default,is_target_variable,created_on,created_by,required'

      id: null
      name: null
      type: null
      feature_set_id: null
      transformer: null
      input_format: null
      params: null
      paramsDict: null
      scaler: null
      default: null
      is_required: false
      is_target_variable: false

      loadFromJSON: (origData) =>
        super origData
        @text = @name
        if origData?
          defaultData = {'feature_id': @id}
          if origData.transformer? && Object.keys(origData.transformer).length
            @transformer = new Transformer(
              _.extend origData.transformer, defaultData)
          else
            @transformer = new Transformer(defaultData)

          if origData.scaler? && Object.keys(origData.scaler).length
            @scaler = new Scaler(
              _.extend origData.scaler, defaultData)
          else
            @scaler = new Scaler(defaultData)

          if origData.required?
            @required = origData.required == true || origData.required == 'True'
          if origData.is_target_variable?
            @is_target_variable = origData.is_target_variable == true || \
              origData.is_target_variable == 'True'

          # if origData.params?
          #   if _.isObject(@params)
          #     @paramsDict = _.clone(@params)
          #   else
          #     @paramsDict = JSON.parse(@params)
          # else
          @paramsDict = {}

      constructor: (opts) ->
        super opts
        @BASE_API_URL = Feature.$get_api_url({
          'feature_set_id': @feature_set_id})

      @$get_api_url: (opts, model) ->
        feature_set_id = opts.feature_set_id
        if model?
          feature_set_id = feature_set_id || model.feature_set_id
        if not feature_set_id
          throw new Error 'feature_set_id is required'
        return "#{settings.apiUrl}features/#{feature_set_id}/items/"

      @$loadAll: (opts) ->
        feature_set_id = opts.feature_set_id
        if not feature_set_id
          throw new Error "Feature Set is required"

        extra = {loaded: true, feature_set_id: feature_set_id}
        resolver = (resp, Model) ->
          {
            objects: (
              new Model(_.extend(obj, extra)) \
              for obj in eval("resp.data.#{Model.prototype.API_FIELDNAME}s"))
            _resp: resp
          }
        @$make_all_request(Feature.$get_api_url({
          'feature_set_id': feature_set_id}),
                           resolver, opts)

      $save: (opts={}) =>
        opts.extraData = {}
        removeItems = opts.removeItems || false
        isTransformerFilled = false
        isScalerFilled = false
        for name in opts.only
          if (name.indexOf "transformer__") == 0 && @transformer
            field = name.slice 13
            val = getVal(eval('this.transformer.' + field))
            if val?
              opts.extraData['transformer-' + field] = val
              isTransformerFilled = true

          if (name.indexOf "scaler__") == 0 && @scaler
            field = name.slice 8
            val = getVal(eval('this.scaler.' + field))
            if val?
              opts.extraData['scaler-' + field] = val
              isScalerFilled = true

        if isTransformerFilled
          opts.extraData['transformer-is_predefined'] = false
        else if removeItems
          opts.extraData['remove_transformer'] = true

        if isScalerFilled
          opts.extraData['scaler-is_predefined'] = false
        else if removeItems
          opts.extraData['remove_scaler'] = true

        @params = $filter('json')(@paramsDict)

        super opts

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)

    return Feature
])


.factory('Param', [
  () ->
    class Param
      name: null
      value: null
      saved: true

      constructor: (opts) ->
        _.extend @, opts

    return Param
])

.factory('NamedFeatureType', [
  '$http'
  '$q'
  'settings'
  '$filter'
  'BaseModel'
  'Param'
  
  ($http, $q, settings, $filter, BaseModel, Param) ->
    class NamedFeatureType extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}features/named_types/"
      BASE_UI_URL: "/features/types/"
      API_FIELDNAME: 'named_type'
      @MAIN_FIELDS: 'id,name,type,input_format,params,created_on,created_by'
      @$TYPES_LIST: ['boolean', 'int', 'float', 'numeric', 'date',
                   'map', 'categorical_label', 'categorical',
                   'text', 'regex', 'composite']
      @LIST_MODEL_NAME: 'named_types'
      LIST_MODEL_NAME: @LIST_MODEL_NAME

      id: null
      name: null
      type: null
      input_format: null
      params: null
      paramsDict: null
      created_on: null
      created_by: null

      loadFromJSON: (origData) =>
        super origData

        if origData?
          if origData.params?
            if _.isObject(@params)
              @paramsDict = _.clone(@params)
            else
              @paramsDict = JSON.parse(@params)
          else
            @paramsDict = {}

      $save: (opts={}) =>
        @params = $filter('json')(@paramsDict)

        super opts

    return NamedFeatureType
])


.factory('Parameters', [
  'settings'
  'BaseModel'

  (settings, BaseModel) ->
    class Parameters extends BaseModel
      API_FIELDNAME: 'configuration'
      BASE_API_URL: "#{settings.apiUrl}features/params"

      $load: (opts) ->
        @$make_request("#{@BASE_API_URL}/", opts)

    return Parameters
])
