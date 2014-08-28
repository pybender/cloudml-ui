require('colors')
mock = require('protractor-http-mock')

class LoginPage
  gotoUrl : ->
    browser.get '/#/auth/login'

  getLoginBtn: ->
    element By.css '.btn-large'

  getUserSpan: ->
    element(By.exactBinding('user.name'))

describe 'Login Page Scenarios', ->
  afterEach ->
    mock.teardown()
    browser.driver.manage().logs().get('browser').then (logs)->
      if logs.length > 0
        console.log "Browser logs for test (" +
          "#{jasmine.getEnv().currentSpec.description}".red +
          ') this test will fail because of the following logs'
        for log in logs
          console.log log
      expect(logs.length).toBe 0

  beforeEach ->
    #

  it 'should load the login page and redirect to odesk on login click', ->
    mock(['auth_get_auth_url', 'auth_authenticate', 'auth_get_user'])

    loginPage = new LoginPage
    loginPage.gotoUrl()
    btn = loginPage.getLoginBtn()
    expect(btn.isPresent()).toBeTruthy()
    btn.click()
    browser.driver.getCurrentUrl().then (url)->
      expect(url.indexOf 'https://www.odesk.com/login?redir=%2Fservices%2Fapi%2Fauth%3Foauth_token%3Df0a32ec8cd4b07b7db76c18854803cde').toBe 0

    # simulating odesk calling us back
    # I don't know why but first call doesn't have auth_get_user mock hooked
    browser.get '/#/auth/callback?oauth_token=f0a32ec8cd4b07b7db76c18854803cde&oauth_verifier=29735d95dfcc4128490a40d9c09fc6fa'
    browser.get '/#/auth/callback?oauth_token=f0a32ec8cd4b07b7db76c18854803cde&oauth_verifier=29735d95dfcc4128490a40d9c09fc6fa'

    userSpan = loginPage.getUserSpan()
    expect(userSpan.isPresent()).toBe true
    expect(userSpan.getInnerHtml()).toEqual 'Protractor Bot'

