module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma

  karma.set
    files: karma.files.concat [
      {pattern: '.tmp/js/config.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/local_config.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/services.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/filters.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/directives.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/controllers.js', watched:true, included:true, served:true}
      {pattern: '.tmp/js/base.js', watched:true, included:true, served:true}

      {pattern: '.tmp/js/**/*.js', watched:true, included:true, served:true}

      {pattern: 'app/assets/partials/**/*.html', watched:true, included:true, served:true}

      # Tests
      'test/unit/canned_responses.coffee'
      'test/unit/phantomjs.quirk.coffee'
      {pattern: 'bower_components/angular-mocks/angular-mocks.js', watched:false, included:true, served:true}
      'test/unit/**/*.spec.coffee',
    ]
    reporters: karma.reporters.concat ['coverage']
    preprocessors:
      '.tmp/js/**/*.js': ['coverage']
      'test/unit/**/*.coffee': ['coffee']
      'app/assets/partials/**/*.html': ['ng-html2js']
    browsers: ['PhantomJS']
    singleRun: true
    autoWatch: false
    coverageReporter:
      reporters: [
        type : 'html',
        dir : 'coverage/'
      ,
        type: 'text-summary'
      ]
