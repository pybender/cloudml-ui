module.exports = (karma)->
  vendorConfig = require '../../vendor.config.coffee'
  vendorFiles = []
  for cdnObj in vendorConfig.cdn
    vendorFiles.push
      pattern: cdnObj.local
      watched: false
      included: true
      served: cdnObj.local.indexOf('http') isnt 0

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
    files: vendorFiles

  # list of files to exclude
    exclude: []

    preprocessors:
      '**/*.coffee': ['coffee']
      'app/assets/partials/**/*.html': ['ng-html2js']

    # test results reporter to use
    # possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
    reporters: ['spec']

    # enable / disable colors in the output (reporters and logs)
    colors: true

    # level of logging
    # possible values: karma.LOG_DISABLE || karma.LOG_ERROR || karma.LOG_WARN || karma.LOG_INFO || karma.LOG_DEBUG
    logLevel: karma.LOG_INFO

    # If browser does not capture in given timeout [ms], kill it
    captureTimeout: 60000

    coffeePreprocessor:
      # options passed to the coffee compiler
      options:
        bare: true
        sourceMap: true

    ngHtml2JsPreprocessor:
      moduleName: 'app.templates'
      stripPrefix: 'app/assets/' # this is very important to avoid directives specs
                                 # from issuing http requests to load the template

# transforming the filenames
#transformPath: (path)->
#  return path.replace(/\.js$/, '.coffee')