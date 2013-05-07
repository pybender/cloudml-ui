'use strict'

### Configuration specific to given environment ###
# See config module for settings and explanations

LOCAL_SETTINGS = {

  apiUrl: 'http://172.27.67.106:5000/api/cloudml/b/v1/'
}

angular.module('app.local_config', []).constant 'settings', LOCAL_SETTINGS
