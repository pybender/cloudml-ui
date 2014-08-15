module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma
  karma.frameworks.push 'browserify'

  karma.files.push '../test/unit/**/*.coffee'
  karma.files.splice 14, 0, 'author/browserified.coffee'
  #karma.files.push '../test/unit/author/app.coffee'

  karma.exclude.push '../test/unit/node/**/*.coffee'
  karma.exclude.push '../test/unit/examiner/tour.coffee'
  karma.preprocessors['author/browserified.coffee'] = ['browserify']

  karma.set
    browsers: ['Chrome']

    browserify:
      extensions: ['.coffee']
    #ignore: [path.join __dirname, 'components/angular-unstable/angular.js']
      transform: ['coffeeify']
      watch: true   # Watches dependencies only (Karma watches the tests)
      debug: false   # Adds source maps to bundle
      noParse: ['jquery'] # Don't parse some modules
