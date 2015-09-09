'use strict'

### Feature specific controllers ###
# strftime for JavaScript

#   Field description (taken from http://tinyurl.com/65s2qw)

#    %a  Locale’s abbreviated weekday name.
#    %A  Locale’s full weekday name.
#    %b  Locale’s abbreviated month name.
#    %B  Locale’s full month name.
#    %c  Locale’s appropriate date and time representation.
#    %d  Day of the month as a decimal number [01,31].
#    %H  Hour (24-hour clock) as a decimal number [00,23].
#    %I  Hour (12-hour clock) as a decimal number [01,12].
#    %j  Day of the year as a decimal number [001,366].
#    %m  Month as a decimal number [01,12].
#    %M  Minute as a decimal number [00,59].
#    %p  Locale’s equivalent of either AM or PM.
#    %S  Second as a decimal number [00,61].
#    %U  Week number of the year (Sunday as the first day of the week) as a
#        decimal number [00,53]. All days in a new year preceding the first
#        Sunday are considered to be in week 0.
#    %w  Weekday as a decimal number [0(Sunday),6].
#    %W  Week number of the year (Monday as the first day of the week) as a
#        decimal number [00,53]. All days in a new year preceding the first
#        Monday are considered to be in week 0.
#    %x  Locale’s appropriate date representation.
#    %X  Locale’s appropriate time representation.
#    %y  Year without century as a decimal number [00,99].
#    %Y  Year with century as a decimal number.
#    %z  UTC time zone offset -HHMM or +HHMM.
#    %Z  Time zone name (no characters if no time zone exists).
#    %%  A literal '%' character.


days = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
    'Saturday'
]

months = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'
]

shortname = (name) ->
    return name.substr(0, 3);

zeropad = (n, size) ->
    n = '' + n
    size = size || 2
    while n.length < size
        n = '0' + n
    return n


twelve = (n) ->
    return if n <= 12 then n else 24 - n

getWeekByMon = (d) ->
    mon = 1
    target  = new Date(d.valueOf())
    target.setHours(0, 0, 0, 0)
    jan1    = new Date(target.getFullYear(), 0, 1)
    dayDiff = (target-jan1) / 86400000 + 1

    if jan1.getDay() is mon
      return Math.ceil(dayDiff / 7)
    else
      mon = if jan1.getDay() is 0 then 2 else 9 - jan1.getDay()
      if dayDiff < mon
        return 0
      else
        monday = new Date(target.getFullYear(), 0, mon, 0, 0, 0, 0)
        dayDiff = (target - monday) / 86400000 + 1
        return Math.ceil(dayDiff / 7)

getWeekBySun = (d) ->
    sun = 0
    target  = new Date(d.valueOf())
    target.setHours(0, 0, 0, 0)
    jan1    = new Date(target.getFullYear(), 0, 1)
    dayDiff = (target-jan1) / 86400000 + 1

    if jan1.getDay() is sun
      return Math.ceil(dayDiff / 7)
    else
      sun = 8 - jan1.getDay()
      if dayDiff < sun
        return 0
      else
        sunday = new Date(target.getFullYear(), 0, sun, 0, 0, 0, 0)
        dayDiff = (target - sunday) / 86400000 + 1
        return Math.ceil(dayDiff / 7)

dayOfYear = (d) ->
    target = new Date(d.valueOf())
    jan1 = new Date(target.getFullYear(), 0, 1)
    day = Math.ceil((target-jan1) / 86400000)
    return day

tzOffset = (date) ->
    min = date.getTimezoneOffset()
    sign = if min < 0 then '-' else '+'
    hour = zeropad(Math.floor(Math.abs(min) / 60))
    mins = zeropad(Math.abs(min) % 60)
    return sign + hour + mins

tzName = (date) ->
    return date.toString().substr(date.toString().length - 4, 3)

strftime = (format, date) ->
    date = new Date(date)
    fields = {
        a: shortname(days[date.getDay()]),
        A: days[date.getDay()],
        b: shortname(months[date.getMonth()]),
        B: months[date.getMonth()],
        c: date.toString(),
        d: zeropad(date.getDate()),
        f: zeropad(date.getMilliseconds()*1000, 6),
        H: zeropad(date.getHours()),
        I: zeropad(twelve(date.getHours())),
        j: zeropad(dayOfYear(date),3),
        m: zeropad(date.getMonth() + 1),
        M: zeropad(date.getMinutes()),
        p: if date.getHours() >= 12 then 'PM' else 'AM',
        S: zeropad(date.getSeconds()),
        U: zeropad(getWeekBySun(date)),
        w: zeropad(date.getDay() + 1),
        W: zeropad(getWeekByMon(date)),
        x: date.toLocaleDateString(),
        X: date.toLocaleTimeString(),
        y: ('' + date.getFullYear()).substr(2, 4),
        Y: '' + date.getFullYear(),
        z: tzOffset(date),
        Z: tzName(date),
        '%' : '%'
    }

    result = ''
    i = 0
    while i < format.length
      if format[i] is '%'
        result = result + fields[format[i + 1]]
        i++
      else
        result = result + format[i]
      i++
    return result


strftimeDate = (pattern, unixdate) ->
    # use strftime because strptime will ignore some pattern pieces on backend
    # anyway, but every pattern will be available on frontend
    return strftime(pattern, unixdate*1000)

angular.module('app.features.controllers.features', ['app.config', ])

# Controller for adding/edditing features fields in separate page.
# template: features/items/edit.html
.controller('FeatureEditCtrl', [
  '$scope'
  '$routeParams'
  '$location'
  'Model'
  'Feature'
  'Transformer'
  'Scaler'
  'Parameters'

($scope, $routeParams, $location, Model, \
Feature, Transformer, Scaler, Parameters) ->
  if not $routeParams.model_id then throw new Error "Specify model id"
  if not $routeParams.set_id then throw new Error "Specify set id"

  $scope.modelObj = new Model({'id': $routeParams.model_id})
  $scope.feature = new Feature({
    feature_set_id: $routeParams.set_id,
    transformer: new Transformer({}),
    scaler: new Scaler({}),
    params: {}
  })

  if $routeParams.feature_id
    $scope.feature.id = $routeParams.feature_id
    $scope.feature.$load(show: Feature.MAIN_FIELDS
    ).then ((opts) ->
      if $scope.feature.type is 'date' && $scope.feature.paramsDict?.pattern?
        $scope.feature.default = strftimeDate($scope.feature.paramsDict.pattern,
                                              $scope.feature.default)
      #
    ), ((opts)->
      $scope.setError(opts, 'loading feature details')
    )

  params = new Parameters()
  params.$load().then ((opts)->
      $scope.configuration = opts.data.configuration
    ), ((opts)->
      $scope.setError(opts, 'loading types and parameters')
    )

  $scope.$watch 'configuration', ->
    typeHasChanged()

  $scope.$watch 'feature.type', ->
    typeHasChanged()

  typeHasChanged = ->
    if not $scope.feature.type or not $scope.configuration
      return

    pType = $scope.configuration.types[$scope.feature.type]
    if !pType?  # it's named feature type, not inline
      $scope.feature.paramsDict = {}
      return

    builtInFields = _.union(pType.required_params, pType.optional_params,
      pType.default_params)

    newParamsDict = {}
    for field in builtInFields
      # we will need to prepare the dict objects (only used in mappings),
      # otherwise leave it to the input controls
      newParamsDict[field] = if $scope.configuration.params[field].type isnt 'dict' then null else {}
    for field in _.intersection(builtInFields, _.keys($scope.feature.paramsDict))
      newParamsDict[field] = $scope.feature.paramsDict[field]

    $scope.feature.paramsDict = newParamsDict

  #  TODO: Could we use SaveObjectCtl?
  $scope.save = (fields) ->
    # Note: We need to delete transformer or scaler when
    # transformer/scaler fields selected, when edditing
    # feature in full details page.

    is_edit = $scope.feature.id != null
    $scope.saving = true
    $scope.savingProgress = '0%'

    _.defer ->
      $scope.savingProgress = '50%'
      $scope.$apply()

    $scope.feature.$save(only: fields, removeItems: true).then (->
      $scope.savingProgress = '100%'
      $location.path($scope.modelObj.objectUrl())\
      .search({'action': 'model:details'})
    ), ((opts) ->
      $scope.err = $scope.setError(opts, "saving")
      $scope.savingProgress = '0%'
    )
])

.controller('TrainIHFieldsController', [
    '$scope'

    ($scope)->
      ###
      Controller to load Train import handler fields if not already loaded
      Expects: $scope.modelObj
      ###

      if $scope.fieldNames
        return

      $scope.modelObj.$load
        show: 'train_import_handler,train_import_handler_type,train_import_handler_id'
      .then ->
        $scope.modelObj.train_import_handler_obj.$listFields()
        .then (opts)->
          fieldNames = []
          if $scope.modelObj.train_import_handler_obj.TYPE is 'JSON'
            fieldNames = opts.objects
          else
            $scope.candidateFields = opts.objects
            fieldNames = (f.name for f in opts.objects)
          $scope.fieldNames = _.sortBy(fieldNames, (f) -> return f.toLowerCase())
        , (opts)->
          console.warn 'failed loading fields for trainer ih',
            $scope.modelObj.train_import_handler_obj, ', errors', opts
      , (opts) ->
        console.warn 'failed loading training ih for model', $scope.modelObj,
          ', errors', opts
  ])

.controller('FeatureNameController', [
    '$scope'

    ($scope)->
      ###
      Controller to support type ahead for editing/adding feature name.
      Expects:  TrainIHFieldsController
      ###

      fieldOnSelect = ($item)->
        field = _.find($scope.candidateFields, (f)-> f.name is $item)
        featureType = null
        if not field?.type?
          return
        if field.type is 'float' or field.type is 'boolean'
          featureType = field.type
        else if field.type is 'integer'
          featureType = 'int'
        else if field.type is 'string'
          featureType = 'text'
        else if field.type is 'json'
          featureType = 'map'

        if featureType
          $scope.feature.type = featureType

      $scope.$watch 'candidateFields', (newVal, oldVal)->
        if newVal
          $scope.fieldOnSelect = fieldOnSelect
  ])

