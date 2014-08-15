module.exports = (karma)->
  karma.set
    # base path, that will be used to resolve files and exclude
    basePath: '../../'

    # frameworks to use
    frameworks: ['jasmine']

    # list of files / patterns to load in the browser
    files: [
      # CDN served files same order as found in app/assets/index.html
      {pattern: 'bower_components/lodash/dist/lodash.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/jquery/jquery.js', watched:false, included:true, served:true}
      #{pattern: 'bootstrap here', watched:false, included:true, served:true}
      #{pattern: 'x-editable here', watched:false, included:true, served:true}
      {pattern: 'bower_components/d3/d3.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular/angular.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-route/angular-route.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-resource/angular-resource.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-cookies/angular-cookies.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-sanitize/angular-sanitize.js', watched:false, included:true, served:true}

      # non CDN files/ served using bower
      {pattern: 'vendor/scripts/console-helper.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/select2/select2.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-bootstrap/ui-bootstrap-tpls-0.11.0.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/angular-ui-select2/src/select2.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/moment/moment.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/codemirror/lib/codemirror.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/codemirror/mode/sql/sql.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/codemirror/mode/xml/xml.js', watched:false, included:true, served:true}
      {pattern: 'bower_components/codemirror/mode/python/python.js', watched:false, included:false, served:true}
      {pattern: 'bower_components/codemirror/mode/javascript/javascript.js', watched:false, included:false, served:true}
      {pattern: 'bower_components/angular-ui-codemirror/ui-codemirror.js', watched:false, included:false, served:true}

      {pattern: 'app/scripts/config.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/local_config.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/services.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/filters.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/directives.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/controllers.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/base.coffee', watched:true, included:true, served:true}

      {pattern: 'app/**/*.coffee', watched:true, included:true, served:true}

      {pattern: 'app/assets/partials/{,*/}*.html', watched:true, included:true, served:true}

      # Testing
      {pattern: 'bower_components/angular-mocks/angular-mocks.js', watched:false, included:true, served:true}
      'test/unit/**/weights.spec.coffee',
    ]

  # list of files to exclude
    exclude: [
    ]

    preprocessors:
      '../**/*.coffee': ['coffee']
      '**/*.html': ['ng-html2js']

    # test results reporter to use
    # possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
    reporters: ['spec']

    # enable / disable colors in the output (reporters and logs)
    colors: true

    # level of logging
    # possible values: karma.LOG_DISABLE || karma.LOG_ERROR || karma.LOG_WARN || karma.LOG_INFO || karma.LOG_DEBUG
    logLevel: karma.LOG_INFO

    # enable / disable watching file and executing tests whenever any file changes
    autoWatch: true

    # If browser does not capture in given timeout [ms], kill it
    captureTimeout: 60000

    # Continuous Integration mode
    # if true, it capture browsers, run tests and exit
    singleRun: false

    browsers: ['Chrome']

    coffeePreprocessor:
      # options passed to the coffee compiler
      options:
        bare: false
        sourceMap: false
# transforming the filenames
#transformPath: (path)->
#  return path.replace(/\.js$/, '.coffee')