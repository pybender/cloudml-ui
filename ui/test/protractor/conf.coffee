exports.config =
  seleniumAddress: 'http://localhost:4444/wd/hub'
  specs: ['../e2e/models.spec.coffee']
  jasmineNodeOpts:
    showColors: true
    isVerbose: true
    defaultTimeoutInterval: 360000
  capabilities:
    browserName: 'chrome'
  #rootElement: 'html'
  onPrepare: ->
    global.By = global.by
    require('protractor-http-mock').config =
      dir: __dirname # Let the plugin know where to find this protractor.conf.js file and your mocks.
      protractorConf: 'conf.coffee'
  mocks:
    default: [] # Specify any default mocks that you would like to load for every test
    dir: 'backend-mocks'    # Specify the location of your mocks relative to the location of the protractor.conf.file
