exports.config =
  # See docs at https://github.com/brunch/brunch/blob/stable/docs/config.md
  modules:
    definition: false
    wrapper: false
  paths:
    'public': '_public'
    watched: ['app', 'vendor', 'bower_components']
  files:
    javascripts:
      joinTo:
        'js/app.js': /^app/
        'js/vendor.js': [
            /^vendor/
            'bower_components/codemirror/lib/codemirror.js'
            'bower_components/codemirror/mode/sql/sql.js'
            'bower_components/codemirror/mode/xml/xml.js'
            'bower_components/codemirror/mode/python/python.js'
            'bower_components/codemirror/mode/javascript/javascript.js'
        ]
        'test/scenarios.js': /^test(\/|\\)e2e/
      order:
        before: [
          'vendor/scripts/console-helper.js'
          'vendor/scripts/jquery-1.8.3.js'

          'vendor/scripts/angular/angular.js'
          'vendor/scripts/angular/angular-resource.js'
          'vendor/scripts/angular/angular-cookies.js'

          'vendor/scripts/bootstrap/bootstrap-transition.js'
          'vendor/scripts/bootstrap/bootstrap-alert.js'
          'vendor/scripts/bootstrap/bootstrap-button.js'
          'vendor/scripts/bootstrap/bootstrap-carousel.js'
          'vendor/scripts/bootstrap/bootstrap-collapse.js'
          'vendor/scripts/bootstrap/bootstrap-dropdown.js'
          'vendor/scripts/bootstrap/bootstrap-modal.js'
          'vendor/scripts/bootstrap/bootstrap-tooltip.js'
          'vendor/scripts/bootstrap/bootstrap-popover.js'
          'vendor/scripts/bootstrap/bootstrap-scrollspy.js'
          'vendor/scripts/bootstrap/bootstrap-tab.js'
          'vendor/scripts/bootstrap/bootstrap-typeahead.js'
          'vendor/scripts/bootstrap/bootstrap-affix.js'
        ]
        after: [
          'bower_components/codemirror/mode/sql/sql.js'
          'bower_components/codemirror/mode/xml/xml.js'
          'bower_components/codemirror/mode/python/python.js'
        ]

    stylesheets:
      joinTo:
        'css/app.css': [
          /^(app|vendor)/
          'bower_components/codemirror/lib/codemirror.css'
        ]
      order:
        before: [
          'bower_components/codemirror/theme/cobalt.css'
        ]
    templates:
      joinTo: 'js/templates.js'

  plugins:
    jade:
      pretty: yes # Adds pretty-indentation whitespaces to output (false by default)

  # Enable or disable minifying of result js / css files.
  # minify: true
