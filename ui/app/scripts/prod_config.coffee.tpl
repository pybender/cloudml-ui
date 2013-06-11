'use strict'

### Configuration specific to given environment ###
# See config module for settings and explanations

LOCAL_SETTINGS = {

  apiUrl: 'http://cloudml.int.odesk.com/api/cloudml/'
  logUrl: 'http://172.27.77.141:5000/cloudml/'
}

angular.module('app.local_config', []).constant 'settings', LOCAL_SETTINGS
