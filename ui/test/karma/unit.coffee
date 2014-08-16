module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma

  karma.set
    files: karma.files.concat [
      {pattern: 'app/scripts/config.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/local_config.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/services.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/filters.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/directives.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/controllers.coffee', watched:true, included:true, served:true}
      {pattern: 'app/scripts/base.coffee', watched:true, included:true, served:true}

      {pattern: 'app/**/*.coffee', watched:true, included:true, served:true}

      {pattern: 'app/assets/partials/**/*.html', watched:true, included:true, served:true}

      # Tests
      'test/unit/canned_responses.coffee',
      {pattern: 'bower_components/angular-mocks/angular-mocks.js', watched:false, included:true, served:true}
      'test/unit/**/weights.spec.coffee',
    ]
    browsers: ['Chrome']
    singleRun: false
    autoWatch: true
