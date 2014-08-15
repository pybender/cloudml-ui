
cmlConfig =
  tmpDir: './.tmp'
  appDir: './app'
  buildDir: './_public'
  vendorDir: './vendor'
  reloadPort: 35729
  servePort: 3333

lrSnippet = require('connect-livereload')({ port: cmlConfig.reloadPort })
mountFolder = (connect, dir) ->
  return connect.static(require('path').resolve(dir))

module.exports = (grunt)->

  #load all grunt tasks
  require('matchdep').filter('grunt-*').forEach(grunt.loadNpmTasks)

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
        files: [
          '<%= cmlConfig.appDir %>/**/*'
        ]
#      html2js:
#        files: ['<%= cmlConfig.appDir %>/assets/partials/**/*.html']
#        tasks: ['html2js:compile', 'index:local']
      index_local:
        files: ['<%= cmlConfig.appDir %>/assets/index.html']
        tasks: ['index:local']

    coffee:
      compile:
        options:
          bare: true
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

#    html2js:
#      compile:
#        options:
#          module: false
#          base: '<%= cmlConfig.appDir %>/assets/'
#        files: [
#          expand: true
#          cwd: '<%= cmlConfig.appDir %>/assets/partials/'
#          src: ['**/*.html']
#          dest: '<%= cmlConfig.tmpDir %>/htmljs'
#          ext: '.html.js'
#        ]

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
        ]
      build:
        files: [
          src: 'bower_components/select2/select2.png'
          dest: '<%= cmlConfig.buildDir %>/css'
          expand: true
          flatten: true
        ,
          expand: true
          cwd: '<%= cmlConfig.tmpDir %>/img'
          dest: '<%= cmlConfig.buildDir %>/img'
          src: ['*']
        ,
          expand: true
          cwd: '<%= cmlConfig.appDir %>/assets'
          dest: '<%= cmlConfig.buildDir %>/'
          src: ['{img,font,partials}/**/*']
        ,
          src: '<%= cmlConfig.tmpDir %>/index.html'
          dest: '<%= cmlConfig.buildDir %>/index.html'
        ]

    useminPrepare:
      html: ['<%= cmlConfig.tmpDir %>/index.html']
      options:
        dest: '<%= cmlConfig.buildDir %>'
        staging: '<%= cmlConfig.buildDir %>/'

    usemin:
      html: ['<%= cmlConfig.tmpDir %>/index.html']

    uglify:
      generated:
        options:
          sourceMap: true

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
              mountFolder(connect, './app/assets')
            ]
    open:
      server:
        url: 'http://127.0.0.1:<%= connect.options.port %>'

    concurrent:
      compile: [
        'coffee'
        'less'
        'copy:compile'
#        'html2js'
      ]
      options:
        limit: 4
        logConcurrentOutput: true

  grunt.initConfig gruntConfig

  grunt.registerTask 'index'
  , """
    Task to build the index file out of development JS file for
    usemin/useminprepare and server to function properly. Instead of adding
    every file manually
    instead of writing every coffee file manually in the index.html for
    usemin, we collect them and write them automatically
    """
  , (target)->
    fs = require('fs')
    globule = require('globule')
    # order is very important here
    files = []
    if target is 'local'
      files.splice(1, 0, '/js/local_config.js')
    else if target is 'production'
      files.splice(1, 0, '/js/prod_config.js')
    else if target is 'staging'
      files.splice(1, 0, '/js/staging_config.js')
    else
      throw Error("Unkown target:#{target}")

#    # partials first for quicker rendering of first page
#    globule.find("#{cmlConfig.appDir}/assets/partials/**/*.html").forEach (file)->
#      newFile = file.replace("#{cmlConfig.appDir}/assets/partials/", 'htmljs/')
#      if newFile not in files
#        files.push newFile.replace('.html', '.html.js')

    files = files.concat [
      '/js/config.js'
      '/js/services.js'
      '/js/filters.js'
      '/js/directives.js'
      '/js/controllers.js'
      '/js/base.js'
    ]

    # coffeescript files
    globule.find("#{cmlConfig.appDir}/scripts/**/*.coffee").forEach (file)->
      newFile = file.replace("#{cmlConfig.appDir}/scripts/", 'js/')
      if newFile not in files
        files.push newFile.replace('.coffee', '.js')

    files.push '/js/app.js'

    filesString = ''
    files.forEach (file)->
      filesString += "        <script src=\"#{file}\"></script>\n"
    index = fs.readFileSync "#{cmlConfig.appDir}/assets/index.html", 'utf8'
    index = index.replace '<!-- grunt build_index DONT ALTER -->', filesString
    fs.writeFileSync "#{cmlConfig.tmpDir}/index.html", index

  grunt.registerTask 'server'
  , """Builds and run a development server"""
  , [
      'clean:server'
      'concurrent:compile'
      'index:local'
      'connect:livereload'
      'open:server'
      'watch'
    ]

  grunt.registerTask 'build'
  , """ Builds a production or staging (targets) to destination:
        #{cmlConfig.buildDir}
    """
  , (target) ->
    grunt.task.run [
      'clean'
      'concurrent:compile'
      'index:' + target
      'useminPrepare'
      'concat:generated'
      'cssmin:generated'
      'uglify:generated'
      'usemin'
      'copy:build'
    ]