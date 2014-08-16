module.exports = (karma)->
  baseKarmaFn = require './base.coffee'
  baseKarmaFn karma

  karma.set
    browsers: ['Chrome']
    singleRun: false
    autoWatch: true
