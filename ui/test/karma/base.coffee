module.exports = (karma)->
  vendorConfig = require '../../vendor.config.coffee'
  vendorFiles = []
  for cdnObj in vendorConfig.cdn
    vendorFiles.push
      pattern: cdnObj.local
      watched: false
      included: true
      served: true

  for bundled in vendorConfig.bundled
    vendorFiles.push
      pattern: bundled
      watched: false
      included: true
      served: true

  karma.set
    # base path, that will be used to resolve files and exclude
    basePath: '../../'

    # frameworks to use
    frameworks: ['jasmine']

    # list of files / patterns to load in the browser
    files: vendorFiles.concat [
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
      'test/unit/canned_responses.coffee',
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
        bare: true
        sourceMap: true
# transforming the filenames
#transformPath: (path)->
#  return path.replace(/\.js$/, '.coffee')