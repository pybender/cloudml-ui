require('colors')

class ModelsPage
  gotoUrl : ->
    browser.get '/#/models'

  getErr: ->
    element(By.exactBinding('err'))

  @addCookie: ->
    # we need a visit before we can set the cookie
    browser.get '/#/auth/login'
    browser.manage().addCookie 'auth-token',
      '%22f0a32ec8-cd4b-07b7-db76-c18854803cde%22', '/', '127.0.0.1'

describe 'Models Page Scenarios', ->
  # These scenarios need the following user to be in the postgresql db
  # insert into "user" (name, uid, odesk_url, email, portrait_32_img, auth_token, created_on, updated_on)
  # values ('Protractor Bot', 'protractor_bot', 'https://www.odesk.com/users/~protractor_bot', 'protractorbot@zozo.com',
  # 'https://odesk-prod-portraits.s3.amazonaws.com/Users:nsoliman:PortraitUrl_32?AWSAccessKeyId=1XVAX3FNQZAFC9GJCFR2&Expires=2147483647&Signature=0htc2JllMUARy962wuWTa0Qk5RY%3D',
  # 'bfdcccec35383e04f59537c3f1a4cf073742e16260688f06812a983a', '2014-08-21 19:45:54.473869', '2014-08-28 00:11:04.689624');

  afterEach ->
    # TODO: nader20140828
    # refactor blowing up on console logs to the XPage class in a base class
    browser.driver.manage().logs().get('browser').then (logs)->
      filteredLogs = []
      for log in logs
        if log.message.indexOf('%7B%7B%20user.portrait_32_img%20%7D%7D 0:0 Failed to load resource') < 0
          filteredLogs.push log
      if filteredLogs.length > 0
        console.log "Browser logs for test (" +
          "#{jasmine.getEnv().currentSpec.description}".red +
          ') this test will fail because of the following logs'
        for log in filteredLogs
          console.log log
      expect(filteredLogs.length).toBe 0

  beforeEach ->
    ModelsPage.addCookie()

  it 'smoke test, should load the models list page', ->
    modelsPage = new ModelsPage
    modelsPage.gotoUrl()
    #expect(modelsPage.getErr().isPresent()).toBe false
    #expect(element(By.css('.alert-error')).getAttribute('style').display).toEqual 'none'
    #browser.debugger()

