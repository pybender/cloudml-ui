
cmlConfig =
  buildDir: './.tmp'
  appDir: './app'
  vendorDir: './vendor'
  reloadPort: 35729
  servePort: 9000

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
        tasks: ['coffee:build']
      livereload:
        options:
          livereload: cmlConfig.reloadPort
        files: [
          '<%= cmlConfig.appDir %>/**/*'
        ]
      html2js:
        files: ['<%= cmlConfig.appDir %>/assets/partials/**/*.html']
        tasks: ['html2js:compile']

    coffee:
      compile:
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
        url: 'http://localhost:<%= connect.options.port %>/<%= cmlConfig.appDir %>/assets/index.html'

    concurrent:
      compile: [
        'coffee'
        'less'
      ]
      options:
        limit: 3
        logConcurrentOutput: true

  grunt.initConfig gruntConfig

  grunt.registerTask 'server', [
      'clean'
      'concurrent:compile'
      'connect:livereload'
      'open:server'
      'watch'
    ]

