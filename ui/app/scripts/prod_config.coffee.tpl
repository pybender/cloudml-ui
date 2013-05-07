'use strict'

### Configuration specific to given environment ###
# See config module for settings and explanations

LOCAL_SETTINGS = {

  apiUrl: 'apiUrl: 'http://172.27.77.141/api/cloudml/'
}

angular.module('app.local_config', []).constant 'settings', LOCAL_SETTINGS
