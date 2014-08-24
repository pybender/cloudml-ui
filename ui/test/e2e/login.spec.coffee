class LoginPage
  gotoUrl : ->
    browser.get '/'

  getLoginBtn: ->
    element By.css '.btn-large'

describe 'Login Page Scenarios', ->
  it 'should load the login page and redirect to odesk on login click', ->
    loginPage = new LoginPage
    loginPage.gotoUrl()
    btn = loginPage.getLoginBtn()
    # should show the login button
    expect(btn.isPresent()).toBeTruthy()
    btn.click()
    browser.getCurrentUrl().then (url)->
      expect(url.indexOf 'https://www.odesk.com/login?redir=%2Fservices%2Fapi%2Fauth%3Foauth_token').toBe 0
