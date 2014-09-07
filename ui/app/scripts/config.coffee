'use strict'

### Configuration ###

SETTINGS = {

  # Base CloudML API
  apiUrl: 'http://172.27.77.141/api/cloudml/'

  apiRequestDefaultHeaders: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

}


angular.module('app.config', []).config(['$provide', ($provide) ->
  # Try to find local settings, use them to override settings above.
  # Similar to Django settings / local_settings paradigm

  try
    angular.module('app.local_config')
  catch e
    console.warn "Couldn't find local settings: #{e.message}"
    angular.module('app.local_config', []).constant('settings', {})

  # Apparently can't define app.local_config dependency for config() inline
  local_settings_injector = angular.injector(['app.local_config'])
  local_settings = local_settings_injector.get('settings')

  $provide.constant 'settings', $.extend SETTINGS, local_settings

  MODEL_FIELDS = [ 'name','status','test_import_handler', 'train_import_handler',
    'train_import_handler_type', 'test_import_handler_type',
    'test_handler_fields', 'labels'].join(',')

  # Main model fields and which ones that are required for train/test dialogs
  $provide.constant 'MODEL_FIELDS', MODEL_FIELDS
  $provide.constant 'FIELDS_BY_SECTION',
    model: ['classifier','features_set_id','segments'].join(',')
    training: [
      'error','weights_synchronized','memory_usage','segments', 'trained_by',
      'trained_on','training_time','datasets', 'train_records_count',
      'trainer_size'
    ].join(',')
    about: [
      'created_on','target_variable','example_id','example_label',
      'updated_on','feature_count','created_by','data_fields',
      'test_handler_fields','tags'
    ].join(',')
    main: MODEL_FIELDS
])

###
  Global Functions for Easy spying on window functions
###
$cml_window_location_reload = ->
  window.location.reload()

$cml_window_location_replace = (v)->
  window.location.replace(v)
