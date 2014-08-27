## Versions

`node --version`
v0.10.28

`npm --version`
1.4.9

`grunt --version`
grunt-cli v0.1.13

`bower --version`
1.3.9

`coffee --version`
CoffeeScript version 1.8.0

## Installation Strategy

We are trying to maintain a minimal number of global node modules. In a perfect
configuration you should only have the following modules in 
`/usr/local/lib/node_modules`
 
- bower
- coffee-script
- grunt-cli
- npm

~~Along similar lines of clean installation. Make sure on production boxes you
do `npm install --production`, never forgetting the **--production** flag to 
avoid installing development dependencies that are not needed on production box.
Same goes with `bower install --production`, to avoid installing bower development
dependencies.~~ We might need dev dependencies if we want to run unit tests on the
production box before releasing.

## Global Modules Installation

This is on as-needed-basis, if you are missing a global dependency listed in
the [Installation Strategy](#installation-strategy) do the following, you will
usually need `sudo`

`sudo npm install -g bower@1.3.9`

`sudo npm install -g coffee-script@1.8.0`

`sudo npm install -g grunt-cli@0.1.13`


## Installation

Change directory to your local cloudml-ui/ui directory and do the following:

`rm -r node_modules bower_components`

`npm install`

`bower cache clean`

`bower install`

## Updating Webdrive
Change directory to your local cloudml-ui/ui directory

Update webdrive to install chrome driver and selenium standalone server

`./node_modules/protractor/bin/webdriver-manager update`

in case webdrive updates fails for any reason, do the follwoing are retry the update

`rm -r ./node_modules/protractor/selenium`


### Grunt Key Tasks and Testing your installation

Change directory to your local cloudml-ui/ui directory

`grunt --help`

This will display grunt available tasks, generally use this when needed.

#### Unit Tests (grunt unit)

`grunt unit`

This should launch a browser/chrome and run the unit tests. It _should_ all pass
:), when done do `CTRL+C`


#### E2E with Protractor (grunt e2e)

**Make sure you are running your local backend**

launched E2E tests

`grunt e2e`

This should launch a browser/chrome and run the E2E tests. It _should_ all pass
:)

#### Running the app during development (grunt server)

`grunt server`

This will run the application and monitors key files for live reload.

You can also do

`grunt server:usecdn` 

If you want to run again CDN version of 3rd parties. By default `grun server` will
run against local 3rd parties files for speed (look at ./vendor.config.coffee for
more details on this)

#### Building \_public

`grunt build`

This will build the distributable files. It will include ./app/scripts/prod_config.coffee 
by default. You can use staging by grunt build:staging, further more you can try
out the built files locally by using grunt build:local and launch a simple server
against _public like

`cd _public`
`python -m SimpleHTTPServer 8080`


#### Coverage

`grunt coverage`

Then open ./coverage/xyz/index.html in browser

## Directory Layout

    _public/                  --> Contains generated file for servering the app
                                  These files should not be edited directly
    app/                      --> all of the files to be used in production

      assets                  --> a place for static assets. These files will be copied to
                                  the public directory un-modified.
        font/                 --> [fontawesome](http://fortawesome.github.com/Font-Awesome/) rendering icons
          fontawesome-webfont.*
        img/                  --> image files
        partials/             --> angular view partials (partial HTML templates)
          nav.html                These files will be compiled using html2js
          partial1.html           These files will be compiled using html2js
          partial2.html
        index.html            --> app layout file (the main html template file of the app).

      scripts/                --> base directory for app scripts
        controllers.js        --> application controllers
        directives.js         --> custom angular directives
        filters.js            --> custom angular filters
        services.js           --> custom angular services

      styles/                 --> all custom styles. Acceptable files types inculde:
                                  less, sass, scss and stylus
        themes/               --> a place for custom themes
          custom/             --> starter theme **NOTE the underscore (_). Files begining with an
                                  underscore will not automatically be compiled, they must be imported.
            _override.less    --> styles that should beloaded after bootstrap.
            _variables.less   --> bootstrap variables to be used during the compilation process
        app.less              --> a file for importing styles.
      app.coffee              --> application definition and routes.
      
    bower_components          --> Bower Components
    coverage                  --> coverage reports when running grunt coverage
    node_modules              --> NodeJS modules

    test/                     --> test source files and libraries
      e2e/                    -->
        *.spec.coffee         --> end-to-end specs to run with protractor
      karma/                 
        base.coffee           --> base module for karma configurations, all other
                                  configurations depends on it
        ci.coffee             --> karma configuration for continuous integration
        coverage.coffee       --> karma configuration for coverage calculation
        unit.coffee           --> karma configuration for unit testing
      protractor/
        conf.coffee           --> protractor configuration
        run-webdirve.sh       --> for running local selenium/webdirve instance manually
                                  generally grunt e2e does that for you
      unit/
        controllers.spec.js   --> specs for controllers
        directives.spec.js    --> specs for directives
        filters.spec.js       --> specs for filters
        services.spec.js      --> specs for services

    vendor/                   --> This is left for backward compatibility, generally
                                  speaking all vendor files should be installed
                                  using bower and referenced in vendor.config.coffee
      scripts/                --> angular and 3rd party javascript libraries
        console-helper.js     --> makes it safe to do `console.log()` always
      styles/                 --> sapling / sapling themes and 3 party CSS
        sapling               --> extends boostrap
          _*.less
        themes                --> themes to extend Bootstrap
          default             --> the default bootstrap theme
            _overrides.less
            _variables.less
          sapling             --> supplemental theme
            _overrides.less
            _variables.less
    bower.json                --> Bower installed components, always make sure
                                  to do bower install xyz --save (or --save-dev)
    Gruntfile.coffee          --> grunt configuration file, use grunt --help to 
                                  get list of available tasks
    package.json              --> npm package configuration file, make sure to
                                  do npm install --save or npm install --save-dev
    README.md                 --> this file
    vendor.config.coffee      --> This file is used to configure app/assets/index.html
                                  with external and local scripts and styles. Read
                                  its comments for more details
