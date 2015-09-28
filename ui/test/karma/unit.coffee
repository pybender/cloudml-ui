module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma

  karma.set
    files: karma.files.concat [
      'app/scripts/config.coffee'
      'app/scripts/local_config.coffee'
      'app/scripts/services.coffee'
      'app/scripts/filters.coffee'
      'app/scripts/directives.coffee'
      'app/scripts/controllers.coffee'
      'app/scripts/base.coffee'

      'app/**/*.coffee'
      'app/assets/partials/**/*.html'

      # Tests
      'test/unit/canned_responses.coffee',
      'test/unit/utils.coffee',
      {pattern: 'bower_components/angular-mocks/angular-mocks.js', watched:false, included:true, served:true}
      'test/unit/**/*.spec.coffee',
    ]
    browsers: ['Chrome']
    singleRun: false
    autoWatch: true
