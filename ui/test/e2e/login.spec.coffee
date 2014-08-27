HttpBackend = require('http-backend-proxy')
require('colors')

class LoginPage
  gotoUrl : ->
    browser.get '/'

  getLoginBtn: ->
    element By.css '.btn-large'

describe 'Login Page Scenarios', ->
  afterEach ->
    browser.driver.manage().logs().get('browser').then (logs)->
      if logs.length > 0
        console.log "Browser logs for test (" +
          "#{jasmine.getEnv().currentSpec.description}".red +
          ') this test will fail because of the following logs'
        for log in logs
          console.log log
      #expect(logs.length).toBe 0

  it 'should load the login page and redirect to odesk on login click', ->
    loginPage = new LoginPage
    loginPage.gotoUrl()
    btn = loginPage.getLoginBtn()
    # should show the login button
    expect(btn.isPresent()).toBeTruthy()
    btn.click()
    browser.getCurrentUrl().then (url)->
      expect(url.indexOf 'https://www.odesk.com/login?redir=%2Fservices%2Fapi%2Fauth%3Foauth_token').toBe 0

  xit 'should successfully login the user', ->
    loginPage = new LoginPage
    loginPage.gotoUrl()

    httpBackend = new HttpBackend(browser)
    httpBackend.whenGET('/cloudml/auth/get_auth_url')
    .respond(200, {auth_url: "https://www.odesk.com/services/api/auth?oauth_token=f0a32ec8cd4b07b7db76c18854803cde"})
    httpBackend.whenGET('https://www.odesk.com/services/api/auth?oauth_token=f0a32ec8cd4b07b7db76c18854803cde')
    .respond(302, '', {Location: 'http://127.0.0.1:3333/#/auth/callback?oauth_token=f0a32ec8cd4b07b7db76c18854803cde&oauth_verifier=29735d95dfcc4128490a40d9c09fc6fa'})

    browser.debugger()

    btn = loginPage.getLoginBtn()
    expect(btn.isPresent()).toBeTruthy()
    btn.click()
