'use strict'

# jasmine specs for helpers go here

describe "helpers", ->
  beforeEach(module "app.helpers")

  describe "shortname", ->

    it "should take 1st 3 letters from name", ->
      expect(shortname("somestr")).toEqual "som"
      expect(shortname("so")).toEqual "so"
      expect(shortname("")).toEqual ""


  describe "zeropad", ->

    it "should add zeros in front of string", ->
      expect(zeropad("1", 4)).toEqual "0001"
      expect(zeropad("22", 2)).toEqual "22"
      expect(zeropad("33", 1)).toEqual "33"
      expect(zeropad("3", 0)).toEqual "03"


  describe "twelve", ->

    it "should make number <= 12 (24 hour format to 12 hour format)", ->
      expect(twelve(23)).toEqual 11
      expect(twelve(11)).toEqual 11
      expect(twelve(0)).toEqual 0


  describe "getWeekByMon", ->

    it "should return week number starting from 1st monday of year, week before 1st Monday is week 0", ->
      expect(getWeekByMon('2001-02-05')).toEqual 6
      expect(getWeekByMon('2002-01-01')).toEqual 0
      expect(getWeekByMon('2002-01-07')).toEqual 1
      expect(getWeekByMon('2012-01-24')).toEqual 4
      expect(getWeekByMon('2001-01-01')).toEqual 1
      expect(getWeekByMon('2002-01-07')).toEqual 1


  describe "getWeekBySun", ->

    it "should return week number starting from 1st sunday of year, week before 1st Sunday is week 0", ->
      expect(getWeekBySun('2001-02-05')).toEqual 5
      expect(getWeekBySun('2011-01-01')).toEqual 0
      expect(getWeekBySun('2012-01-07')).toEqual 1
      expect(getWeekBySun('2012-01-01')).toEqual 1
      expect(getWeekBySun('2012-01-24')).toEqual 4
      expect(getWeekBySun('2002-01-07')).toEqual 1


  describe "dayOfYear", ->

    it "should return day number starting from the beginning of year, 1st Jan is day 1", ->
      expect(dayOfYear('2001-01-01')).toEqual 1
      expect(dayOfYear('2012-03-01')).toEqual 61
      expect(dayOfYear('2011-03-01')).toEqual 60
      expect(dayOfYear('2012-12-31')).toEqual 366
      expect(dayOfYear('2011-12-31')).toEqual 365


  describe "tzOffset", ->

    it "should return time zone offset in format +/-HHMM", ->
      d = new Date('2001-01-01')
      offset = d.getTimezoneOffset()
      calculated = tzOffset(d)
      minutes = (parseInt(calculated.substr(1, 2))*60 + parseInt(calculated.substr(3, 2)))*parseInt(calculated.substr(0,1)+"1")
      expect(minutes).toEqual offset


  describe "tzName", ->

    it "should return time zone name in format +/-HHMM", ->
      d = new Date('2001-01-01')
      offset = d.getTimezoneOffset()
      calculated = tzOffset(d)
      minutes = (parseInt(calculated.substr(1, 2))*60 + parseInt(calculated.substr(3, 2)))*parseInt(calculated.substr(0,1)+"1")
      expect(minutes).toEqual offset


  describe "strftime", ->

    it "should return time according to given pattern", ->
      expect(strftime('%y year %m month(%b) %d day %I:%M:%S %p, %a, %j day of year, week %U(by Sun) %W(by Mon)',
                      '2015-03-04 23:12:13')).toEqual "15 year 03 month(Mar) 04 day 11:12:13 PM, Wed, 063 day of year, week 09(by Sun) 09(by Mon)"


  describe "strftimeDate", ->

    it "should return time according to given pattern", ->
      expect(strftimeDate('%Y year %m month(%b) %d day, %a, %j day of year, week %U(by Sun) %W(by Mon)',
                          946684800)).toEqual "2000 year 01 month(Jan) 01 day, Sat, 001 day of year, week 00(by Sun) 00(by Mon)"


  describe "JSON2CSV", ->

    it "should transform JSON to CSV format",  ->
      expect(JSON2CSV([{file: "xx", m: "yy"}, {file: "zz", m: "bb"}])).toEqual 'file,m\r\nxx,yy\r\nzz,bb\r\n'
      expect(JSON2CSV([{file: "xx", m: [["yy", "kk"], ["ll", "oo"]]}])).toEqual 'file,m\r\nxx,"[yy,kk], [ll,oo]"\r\n'
      expect(JSON2CSV([{file: "xx", m: ["yy", "kk"]}])).toEqual 'file,m\r\nxx,"yy, kk"\r\n'
      expect(JSON2CSV(null)).toEqual 'There is an issue in JSON response. Content can not be transformed to CSV'
