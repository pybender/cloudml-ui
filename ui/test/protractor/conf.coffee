exports.config =
  seleniumAddress: 'http://localhost:4444/wd/hub'
  specs: ['../e2e/*.spec.coffee']
  jasmineNodeOpts:
    showColors: true
    isVerbose: true
  capabilities:
    browserName: 'chrome'
  onPrepare: ->
    global.By = global.by
  #rootElement: 'html'


