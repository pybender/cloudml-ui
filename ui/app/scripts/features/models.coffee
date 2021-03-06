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

removeDefaults = (model) ->
  if model.config?.parameters?
    for param in model.config.parameters
      if model.params[param.name]? && model.params[param.name] == param.default
        delete model.params[param.name]
  return model.params


angular.module('app.features.models', ['app.config'])

.factory('Transformer', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  'XmlImportHandler'
  
  ($http, $q, settings, BaseModel, XmlImportHandler) ->
    class Transformer extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}transformers/"
      BASE_UI_URL: "/predefined/transformers"
      API_FIELDNAME: 'transformer'
      @LIST_MODEL_NAME: 'transformers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: ['id', 'name', 'type', 'params', 'created_on', 'created_by',
                     'status', 'train_import_handler_type',
                     'train_import_handler', 'training_in_progress'].join(',')
      @$TYPES_LIST: ['Dictionary', 'Count', 'Tfidf', 'Lda', 'Lsi', 'Ntile',
                     'Word2Vec', 'Doc2Vec']


      id: null
      name: null
      type: null
      params: null

      loadFromJSON: (origData) ->
        super origData

        if origData?
          if origData.train_import_handler?
            if origData.train_import_handler_type == 'xml'
              cls = XmlImportHandler
            else
              throw new Error('Need to load import handler type')
            @train_import_handler_obj = new cls(
              origData['train_import_handler'])
            @train_import_handler = @train_import_handler_obj.id
          if origData.json?
            @json = angular.toJson(origData.json, pretty=true)

      $getConfiguration: (opts={}) =>
        @$make_request("#{@BASE_API_URL}#{@id}/action/configuration/",
                       load=false)
      $train: (opts={}) ->
        data = {}
        for key, val of opts
          if key == 'parameters' then val = JSON.stringify(val)
          data[key] = val
        @$make_request("#{@BASE_API_URL}#{@id}/action/train/", {}, "PUT", data)

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
      @$TYPES_LIST: ['MinMaxScaler', 'StandardScaler', 'NoScaler']

      id: null
      name: null
      type: null

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
      BASE_UI_URL: "/features/classifiers"
      API_FIELDNAME: 'classifier'
      @LIST_MODEL_NAME: 'classifiers'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      @MAIN_FIELDS: 'id,name,type,created_on,created_by,params'
      @$TYPES_LIST: ['stochastic gradient descent classifier',
      'support vector regression', 'logistic regression',
      'decision trees classifier', 'decision tree regressor']

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
      BASE_UI_URL: "/features/sets"
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
            #console.log @group_by

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
      @MAIN_FIELDS: ['id','name','type','input_format','transformer','params',
                     'scaler','default','is_target_variable','created_on',
                     'created_by','required', 'disabled'].join(',')

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
          else if not @transformer # when partial saving don't reset the transformer
            @transformer = new Transformer(defaultData)

          if origData.scaler? && Object.keys(origData.scaler).length
            @scaler = new Scaler(
              _.extend origData.scaler, defaultData)
          else if not @scaler # when partial saving don't reset the scaler
            @scaler = new Scaler(defaultData)

          if origData.required?
            @required = origData.required == true || origData.required == 'True'
          if origData.is_target_variable?
            @is_target_variable = origData.is_target_variable == true || \
              origData.is_target_variable == 'True'

          if origData.params?
             if _.isObject(@params)
               @paramsDict = _.clone(@params)
             else
               @paramsDict = JSON.parse(@params)
          else
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
        if 'transformer' in opts.only
          _.remove opts.only, (x)-> x is 'transformer'
          transType = @transformer.type
          transId = @transformer.id
          transParams = removeDefaults(@transformer)

          if (transId? and transId is 0) or not transType
            opts.extraData['remove_transformer'] = true
          else
            opts.extraData['remove_transformer'] = false
            if transId > 0
              opts.extraData['transformer-predefined_selected'] = true
              opts.extraData['transformer-transformer'] = transId
            else
              opts.extraData['transformer-predefined_selected'] = false
              opts.extraData['transformer-type'] = transType
              opts.extraData['transformer-params'] = angular.toJson(transParams)

        if 'scaler' in opts.only
          _.remove opts.only, (x)-> x is 'scaler'
          scalerType = @scaler.type
          scalerName = @scaler.name
          predefined = @scaler.predefined
          scalerParams = removeDefaults(@scaler)

          if not scalerType and not scalerName
            opts.extraData['remove_scaler'] = true
          else
            opts.extraData['remove_scaler'] = false
            if predefined
              opts.extraData['scaler-predefined_selected'] = true
              opts.extraData['scaler-scaler'] = scalerName
            else
              opts.extraData['scaler-predefined_selected'] = false
              opts.extraData['scaler-type'] = scalerType
              opts.extraData['scaler-params'] = angular.toJson(scalerParams)

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
      BASE_UI_URL: "/features/types"
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
