module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma

  karma.set
    browsers: ['PhantomJS']
    singleRun: true
    autoWatch: false
