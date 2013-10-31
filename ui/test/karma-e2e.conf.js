// Karma configuration
// Generated on Wed Aug 28 2013 19:35:25 GMT+0400 (MSK)

module.exports = function(config){
    config.set({

    basePath : '../',

    files : [
      'test/e2e/**/*.coffee'
    ],

    autoWatch: false,

    browsers: ['PhantomJS'],

    frameworks: ['ng-scenario'],

    singleRun: true,

    proxies : {
      '/': 'http://localhost:3333/'
    },

    urlRoot: '/__karma__/',

    plugins: [
      // these plugins will be require() by Karma
      'karma-jasmine',
      'karma-firefox-launcher',
      'karma-chrome-launcher',
      'karma-phantomjs-launcher',
      'karma-coffee-preprocessor',
      'karma-ng-scenario'
    ]

});
};