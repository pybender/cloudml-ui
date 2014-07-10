'use strict'

### Configuration ###

SETTINGS = {

  # Base CloudML API
  apiUrl: 'http://172.27.77.141/api/cloudml/'

  apiRequestDefaultHeaders: {
    'Content-Type': 'application/x-www-form-urlencoded'
    'X-Requested-With': null
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
])

###
  Global Functions for Easy spying on window functions
###
$cml_window_location_reload = ->
  window.location.reload()

$cml_window_location_replace = (v)->
  window.location.replace()
