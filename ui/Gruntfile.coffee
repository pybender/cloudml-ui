
cmlConfig =
  buildDir: './.tmp'
  appDir: './app'
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
      html2js:
        files: ['<%= cmlConfig.appDir %>/assets/partials/**/*.html']
        tasks: ['html2js:compile', 'index:local']
      index_html:
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
          dest: '<%= cmlConfig.buildDir %>/js'
          ext: '.js'
        ,
          expand: true,
          cwd: '<%= cmlConfig.appDir %>/scripts'
          src: ['**/*.coffee']
          dest: '<%= cmlConfig.buildDir %>/js'
          ext: '.js'
        ]

    html2js:
      compile:
        options:
          module: null # no bundle module for all the html2js templates
          base: '<%= cmlConfig.appDir %>/assets/'
        files: [
          expand: true
          cwd: '<%= cmlConfig.appDir %>/assets/partials/'
          src: ['**/*.html']
          dest: '<%= cmlConfig.buildDir %>/js.html'
          ext: '.html.js'
        ]

    less:
      compile:
        files: [
          expand: true,
          cwd: '<%= cmlConfig.appDir %>/styles'
          src: ['*.less']
          dest: '<%= cmlConfig.buildDir %>/css'
          ext: '.css'
        ]

    copy:
      compile:
        files: [
          src: '<%= cmlConfig.appDir %>/assets/img/books-icon.png'
          dest: '<%= cmlConfig.buildDir %>/img/'
          expand: true
          flatten: true
        ,
          src: 'bower_components/select2/select2.png'
          dest: '<%= cmlConfig.buildDir %>/img/'
          expand: true
          flatten: true
        ,
          src: 'bower_components/bootstrap/img/glyphicons-halflings.png'
          dest: '<%= cmlConfig.buildDir %>/img/'
          expand: true
          flatten: true
        ,
          src: 'bower_components/bootstrap/img/glyphicons-halflings-white.png'
          dest: '<%= cmlConfig.buildDir %>/img/'
          expand: true
          flatten: true
        ,
          src: '<%= cmlConfig.appDir %>/assets/font/*'
          dest: '<%= cmlConfig.buildDir %>/font/'
          expand: true
          flatten: true
        ]

    useminPrepare:
      html: ['<%= cmlConfig.appDir %>/assets/index.html']
      options:
        dest: '<%= cmlConfig.buildDir %>'

    usemin:
      html: ['<%= cmlConfig.buildDir %>/index.html']
      #css: ['<%= yeoman.dist %>/styles/{,*/}*.css']
      options:
        dirs: ['<%= cmlConfig.buildDir %>']

    clean:
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
              mountFolder(connect, cmlConfig.buildDir)
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
        'copy'
      ]
      options:
        limit: 3
        logConcurrentOutput: true

  grunt.initConfig gruntConfig

  grunt.registerTask 'index', (target)->
    ###
    instead of writing every coffee file manually in the index.html for
    usemin, we collect them and write them automatically
    ###
    fs = require('fs')
    globule = require('globule')
    files = [
      '/js/config.js'
      '/js/services.js'
      '/js/filters.js'
      '/js/directives.js'
      '/js/controllers.js'
      '/js/base.js'
      '/js/app.js'
    ]
    if target is 'local'
      files.splice(1, 0, '/js/local_config.js')
    else if target is 'prod'
      files.splice(1, 0, '/js/prod_config.js')
    else if target is 'staging'
      files.splice(1, 0, '/js/staging_config.js')
    else
      throw Error("Unkown target:#{target}")
    globule.find("#{cmlConfig.appDir}/scripts/**/*.coffee").forEach (file)->
      newFile = file.replace('./app/scripts/', 'js/')
      newFile = newFile.replace('.coffee', '.js')
      if newFile not in files
        files.splice(files.length - 1, 0, newFile)
    filesString = ''
    files.forEach (file)->
      filesString += "        <script src=\"#{file}\"></script>\n"
    index = fs.readFileSync "#{cmlConfig.appDir}/assets/index.html", 'utf8'
    index = index.replace '<!-- grunt build_index DONT ALTER -->', filesString
    fs.writeFileSync "#{cmlConfig.buildDir}/index.html", index

  grunt.registerTask 'server', [
      'clean'
      'concurrent:compile'
      'index:local'
      'connect:livereload'
      'open:server'
      'watch'
    ]