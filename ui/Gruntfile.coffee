
cmlConfig =
  tmpDir: './.tmp'
  appDir: './app'
  buildDir: './_public'
  vendorDir: './vendor'
  reloadPort: 35729 # port for reloading frontend on watch trigger
  servePort: 3333   # port for serving frontend
  backendPort: '5000' # RESTful API backend port, will be running on http:/127.0.0.1:5001
  backendRoot: '../'
  backendPython: '/home/nader/.venvs/odesk_dev/bin/python' # use full path to virtualenv python

lrSnippet = require('connect-livereload')({ port: cmlConfig.reloadPort })
mountFolder = (connect, dir) ->
  return connect.static(require('path').resolve(dir))

module.exports = (grunt)->
  #load all grunt tasks
  require('matchdep').filter('grunt-*').forEach(grunt.loadNpmTasks)
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks)

  gruntConfig =
    cmlConfig: cmlConfig
    watch:
      coffee:
        files: ['<%= cmlConfig.appDir %>/app.coffee',
                '<%= cmlConfig.appDir %>/scripts/**/*.coffee'
        ]
        tasks: ['coffee:compile', 'index:local']
      livereload:
        options:
          livereload: cmlConfig.reloadPort
        files: ['<%= cmlConfig.appDir %>/**/*',
                'vendor.config.coffee']
      html2js:
        files: ['<%= cmlConfig.appDir %>/assets/partials/**/*.html']
        tasks: ['html2js:compile', 'index:local']
      index_local:
        files: ['<%= cmlConfig.appDir %>/assets/index.html',
                'vendor.config.coffee']
        tasks: ['index:local']

    coffee:
      compile:
        options:
          bare: true
          sourceMap: true
        files: [
          expand: true,
          cwd: '<%= cmlConfig.appDir %>'
          src: ['app.coffee']
          dest: '<%= cmlConfig.tmpDir %>/js'
          ext: '.js'
        ,
          expand: true,
          cwd: '<%= cmlConfig.appDir %>/scripts'
          src: ['**/*.coffee']
          dest: '<%= cmlConfig.tmpDir %>/js'
          ext: '.js'
        ]

    html2js:
      options:
        module: 'app.templates'
        base: '<%= cmlConfig.appDir %>/assets'
      compile:
        src: ['<%= cmlConfig.appDir %>/assets/partials/**/*.html'],
        dest: '<%= cmlConfig.tmpDir %>/js/partials.html.js'

    less:
      compile:
        files: [
          expand: true,
          cwd: '<%= cmlConfig.appDir %>/styles'
          src: ['*.less']
          dest: '<%= cmlConfig.tmpDir %>/css'
          ext: '.css'
        ]

    copy:
      compile:
        files: [
          src: 'bower_components/bootstrap/img/glyphicons-halflings.png'
          dest: '<%= cmlConfig.tmpDir %>/img/'
          expand: true
          flatten: true
        ,
          src: 'bower_components/bootstrap/img/glyphicons-halflings-white.png'
          dest: '<%= cmlConfig.tmpDir %>/img/'
          expand: true
          flatten: true
        ,
          expand: true
          cwd: '<%= cmlConfig.appDir %>/assets'
          dest: '<%= cmlConfig.tmpDir %>/'
          src: ['{img,font}/**/*']
        ]
      build:
        files: [
          src: 'bower_components/select2/select2.png'
          dest: '<%= cmlConfig.buildDir %>/css'
          expand: true
          flatten: true
        ,
          expand: true
          cwd: '<%= cmlConfig.tmpDir %>'
          dest: '<%= cmlConfig.buildDir %>'
          src: ['{img,font}/**/*']
        ,
          src: '<%= cmlConfig.tmpDir %>/index.html'
          dest: '<%= cmlConfig.buildDir %>/index.html'
        ]

    useminPrepare:
      html: ['<%= cmlConfig.buildDir %>/index.html']
      options:
        dest: '<%= cmlConfig.buildDir %>'
        staging: '<%= cmlConfig.buildDir %>/'

    usemin:
      html: '<%= cmlConfig.buildDir %>/index.html'

    uglify:
      generated:
        options:
          sourceMap: true

    filerev:
      source:
        files: [
          src: [
            '<%= cmlConfig.buildDir %>/js/*.js'
            '<%= cmlConfig.buildDir %>/css/*.css'
          ]
        ]

    clean:
      server:
        files: [
          dot: true,
          src: ['<%= cmlConfig.tmpDir %>']
        ]
      build:
        files: [
          dot: true,
          src: ['<%= cmlConfig.buildDir %>']
        ]

    connect:
      options:
        port: cmlConfig.servePort,
        hostname: '127.0.0.1'
      livereload:
        options:
          middleware: (connect) ->
            return [
              lrSnippet
              mountFolder(connect, cmlConfig.tmpDir)
              mountFolder(connect, '.')
            ]
    open:
      server:
        url: 'http://127.0.0.1:<%= cmlConfig.servePort %>'

    concurrent:
      compile: [
        'coffee'
        'less'
        'copy:compile'
        'html2js'
      ]
      e2e: [
        'protractor_webdriver:e2e'
        #'backend' #run the backend yourself :)
      ]
      options:
        limit: 4
        logConcurrentOutput: true

    karma:
      unit:
        configFile: 'test/karma/unit.coffee'
      coverage:
        configFile: 'test/karma/coverage.coffee'

    protractor_webdriver:
      options:
        path: './node_modules/protractor/bin/'
      e2e:
        {}

    protractor:
      options:
        keepAlive: true # If false, the grunt process stops when the test fails.
        noColor: false
      e2e:
        options:
          configFile: './test/protractor/conf.coffee'
          #debug: true
          args:
            baseUrl: "http://127.0.0.1:#{cmlConfig.servePort}"

  grunt.initConfig gruntConfig

  grunt.registerTask 'index'
  , """
    Task to build the index file out of development JS file for
    usemin/useminprepare and the server target to function properly.
    Instead of adding every file manually in the index.html for usemin, we
    collect them and write them automatically.
    It also supplies CDN and bundled files as per vendor.config.coffee
    The files will be resolved against ./.tmp where they are generated

    @target: can be one of local, production, staging
    @usecdn: can be usecdn, valid only for local target, default ''
    """
  , (target, usecdn)->
    fs = require('fs')
    indexFileStr = fs.readFileSync "#{cmlConfig.appDir}/assets/index.html", 'utf8'
    vendorConfig = require './vendor.config.coffee'

    replaceTokenWith = (token, replacement) ->
      indexFileStr = indexFileStr.replace token, replacement

    putConvertedFiles = ->
      globule = require('globule')
      # order is very important here
      files = [
        '/js/partials.html.js'
        '/js/config.js'
        '/js/services.js'
        '/js/filters.js'
        '/js/directives.js'
        '/js/controllers.js'
        '/js/base.js'
      ]

      if target is 'local'
        files.splice(2, 0, '/js/local_config.js')
      else if target is 'production'
        files.splice(2, 0, '/js/prod_config.js')
      else if target is 'staging'
        files.splice(2, 0, '/js/staging_config.js')
      else
        throw Error("Unkown target:#{target}")

      # coffeescript files
      globule.find("#{cmlConfig.appDir}/scripts/**/*.coffee").forEach (file)->
        newFile = file.replace("#{cmlConfig.appDir}/scripts/", 'js/')
        if newFile not in files
          files.push newFile.replace('.coffee', '.js')

      files.push '/js/app.js'

      filesString = ''
      for file in files
        preamble = if file is files[0] then '' else '    '
        filesString += "#{preamble}<script src=\"#{file}\"></script>\n"

      replaceTokenWith /<!-- TAG_CONVERTED -->[^]+TAG_CONVERTED -->/g, filesString

    putVendorCDNFiles = ->
      filesString = ''
      for cdnObj in vendorConfig.cdn
        preamble = if cdnObj is vendorConfig.cdn[0] then '' else '    '
        if target is 'local' and usecdn is 'usecdn'
          cdnUrl = cdnObj.notmin
        else if target is 'local'
          cdnUrl = cdnObj.local
        else
          cdnUrl = cdnObj.external
        filesString += "#{preamble}<script src=\"#{cdnUrl}\"></script>\n"
      replaceTokenWith /<!-- TAG_CDN -->[^]+TAG_CDN -->/g, filesString

    putVendorBundledFiles = ->
      filesString = ''
      for bundled in vendorConfig.bundled
        preamble = if bundled is vendorConfig.bundled[0] then '' else '    '
        filesString += "#{preamble}<script src=\"../#{bundled}\"></script>\n"
      replaceTokenWith /<!-- TAG_BUNDLED -->[^]+TAG_BUNDLED -->/g, filesString

    putConvertedFiles()
    putVendorCDNFiles()
    putVendorBundledFiles()
    fs.writeFileSync "#{cmlConfig.tmpDir}/index.html", indexFileStr

#  grunt.registerTask 'backend'
#  , """Runs backend for E2E tests"""
#  , ->
#    # TODO: we need to figure out away to kill the process after grunt finishes
#    spawn = require('child_process').spawn
#    args = ["#{cmlConfig.backendRoot}manage.py", 'runserver',
#            '-p', cmlConfig.backendPort]
#    grunt.log.writeln("Starting backend with #{cmlConfig.backendPython} and
#arguments: #{args}")
#    PIPE = {stdio: 'inherit'}
#    child = spawn cmlConfig.backendPython, args, PIPE
##    process.on 'removeListener', (event, fn) ->
##      # Grunt uses node-exit [0], which eats process 'exit' event handlers.
##      # Instead, listen for an implementation detail: When Grunt shuts down, it
##      # removes some 'uncaughtException' event handlers that contain the string
##      # 'TASK_FAILURE'. Super hacky, but it works.
##      # [0]: https://github.com/cowboy/node-exit
##      if event is 'uncaughtException' and fn.toString().match(/TASK_FAILURE/)
##        grunt.log.writeln 'killing backend server'
##        child.kill()

  grunt.registerTask 'server'
  , """Builds and run a development server"""
  , (target)->
    target = if target is 'usecdn' then ':usecdn' else ''
    grunt.task.run [
      'clean:server'
      'concurrent:compile'
      'index:local' + target
      'connect:livereload'
      'open:server'
      'watch'
    ]

  grunt.registerTask 'build'
  , """ Builds a production or staging (targets) to destination:
        #{cmlConfig.buildDir}
    """
  , (target) ->
    target = if target then target else 'production'
    grunt.task.run [
      'clean'
      'concurrent:compile'
      'index:' + target
      'copy:build'
      'useminPrepare'
      'concat:generated'
      'cssmin:generated'
      'uglify:generated'
      'filerev'
      'usemin'
    ]

  grunt.registerTask 'coverage'
  , """
    Creates coverage report on compiled JS files
    """
  , [
      'clean:server'
      'concurrent:compile'
      'karma:coverage'
    ]

  grunt.registerTask 'unit'
  , """
    Runs Karma Unit Tests
    """
  , [
      'karma:unit'
    ]

  grunt.registerTask 'e2e'
  , """
    Runs Protractor E2E Tests, you should be running backend server at port:#{cmlConfig.backendPort}
    and running frontend server at port:#{cmlConfig.servePort}
    """
  , [
      'concurrent:e2e'
      'protractor:e2e'
    ]

  grunt.registerTask 'ci'
  , """
    Runs Karma Continuous Integration Tests
    """
  , [
      'karma:unit'
    ]