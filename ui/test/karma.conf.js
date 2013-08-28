// Karma configuration
// Generated on Wed Aug 28 2013 19:35:25 GMT+0400 (MSK)

module.exports = function(config) {
  config.set({

    // base path, that will be used to resolve files and exclude
    basePath: '../',


    // frameworks to use
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browser
    files: [
      // Application Code //
      'vendor/scripts/angular/angular.js',
      'vendor/scripts/angular/angular-*.js',
      'vendor/scripts/*.js',
      'vendor/scripts/bootstrap/bootstrap-tooltip.js',
      'vendor/scripts/bootstrap/bootstrap-*.js',

      'app/**/*.coffee',

      // Javascript //
      'test/vendor/angular/angular-mocks.js',

      'test/unit/*.spec.coffee'
    ],


    // list of files to exclude
    exclude: [
      'vendor/scripts/bootstrap-editable.min.js'
    ],

    // compile coffee scripts
    preprocessors: {
      'app/**/*.coffee': ['coffee'],  //, 'coverage'],
      'test/unit/*.spec.coffee': 'coffee'
    },

    // test results reporter to use
    // possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
    reporters: ['spec', 'coverage'],

    // optionally, configure the reporter
    coverageReporter: {
      type : 'html',
      dir : 'test/coverage/'
    },

    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // Start these browsers, currently available:
    // - Chrome
    // - ChromeCanary
    // - Firefox
    // - Opera
    // - Safari (only Mac)
    // - PhantomJS
    // - IE (only Windows)
    browsers: ['PhantomJS'],

    plugins: [
      // these plugins will be require() by Karma
      'karma-jasmine',
      'karma-firefox-launcher',
      'karma-chrome-launcher',
      'karma-coffee-preprocessor',
      'karma-coverage',
      'karma-phantomjs-launcher',
      'karma-spec-reporter'
    ],


    // If browser does not capture in given timeout [ms], kill it
    captureTimeout: 60000,


    // Continuous Integration mode
    // if true, it capture browsers, run tests and exit
    singleRun: true
  });
};
