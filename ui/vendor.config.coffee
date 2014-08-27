module.exports =
  # The following files will be served from CDN generally speaking
  # grunt build:production, grunt build:staging will use external entry
  # grunt server will use local entry, grunt server:usecdn will use notmin entry
  cdn: [
      external:
        "https://cdnjs.cloudflare.com/ajax/libs/lodash.js/2.4.1/lodash.min.js"
      notmin:
        "https://cdnjs.cloudflare.com/ajax/libs/lodash.js/2.4.1/lodash.js"
      local:
        "bower_components/lodash/dist/lodash.js"
    ,
      external:
        "https://cdnjs.cloudflare.com/ajax/libs/jquery/1.8.3/jquery.min.js"
      notmin:
        "https://cdnjs.cloudflare.com/ajax/libs/jquery/1.8.3/jquery.js"
      local:
        "bower_components/jquery/jquery.js"
    ,
      external:
        "https://maxcdn.bootstrapcdn.com/bootstrap/2.3.0/js/bootstrap.min.js"
      notmin:
        "https://maxcdn.bootstrapcdn.com/bootstrap/2.3.0/js/bootstrap.js"
      local:
        "bower_components/bootstrap/docs/assets/js/bootstrap.js"
    ,
      external:
        "https://cdnjs.cloudflare.com/ajax/libs/x-editable/1.4.4/bootstrap-editable/js/bootstrap-editable.min.js"
      notmin:
        "https://cdnjs.cloudflare.com/ajax/libs/x-editable/1.4.4/bootstrap-editable/js/bootstrap-editable.js"
      local:
        "bower_components/x-editable/dist/bootstrap-editable/js/bootstrap-editable.js"
    ,
      external:
        "https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.11/d3.min.js"
      notmin:
        "https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.11/d3.js"
      local:
        "bower_components/d3/d3.js"
    ,
      external:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular.min.js"
      notmin:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular.js"
      local:
        "bower_components/angular/angular.js"
    ,
      external:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-route.min.js"
      notmin:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-route.js"
      local:
        "bower_components/angular-route/angular-route.js"
    ,
      external:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-resource.min.js"
      notmin:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-resource.js"
      local:
        "bower_components/angular-resource/angular-resource.js"
    ,
      external:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-cookies.min.js"
      notmin:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-cookies.js"
      local:
        "bower_components/angular-cookies/angular-cookies.js"
    ,
      external:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-sanitize.min.js"
      notmin:
        "https://ajax.googleapis.com/ajax/libs/angularjs/1.2.20/angular-sanitize.js"
      local:
        "bower_components/angular-sanitize/angular-sanitize.js"
  ]
  # The following files will be minified and uglified into vendor.js
  bundled: [
    "vendor/scripts/console-helper.js"
    "bower_components/select2/select2.js"
    "bower_components/angular-bootstrap/ui-bootstrap-tpls-0.8.0.js"
    "bower_components/angular-ui-select2/src/select2.js"
    "bower_components/moment/moment.js"
    "bower_components/codemirror/lib/codemirror.js"
    "bower_components/codemirror/mode/sql/sql.js"
    "bower_components/codemirror/mode/xml/xml.js"
    "bower_components/codemirror/mode/python/python.js"
    "bower_components/codemirror/mode/javascript/javascript.js"
    "bower_components/angular-ui-codemirror/ui-codemirror.js"
    "bower_components/nvd3/nv.d3.js"
  ]