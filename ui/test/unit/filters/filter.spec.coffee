'use strict'

# jasmine specs for filters go here

describe "filter", ->
  beforeEach(module "app.filters")

  describe "interpolate", ->

    beforeEach(module(($provide) ->
      $provide.value "version", "TEST_VER"
      return
    ))

    it "should replace VERSION", inject((interpolateFilter) ->
      expect(interpolateFilter("before %VERSION% after")).toEqual "before TEST_VER after"
    )

  describe "capfirst", ->

    it "should make the first letter uppercase", inject((capfirstFilter) ->
      expect(capfirstFilter("somestr")).toEqual("Somestr")
      expect(capfirstFilter("Somestr")).toEqual("Somestr")
      expect(capfirstFilter("someStr")).toEqual("SomeStr")
    )

  describe "to_lower", ->

    it "should make the first letter uppercase", inject((to_lowerFilter) ->
      expect(to_lowerFilter("somestr")).toEqual("somestr")
      expect(to_lowerFilter("Somestr")).toEqual("somestr")
      expect(to_lowerFilter("someStr")).toEqual("somestr")
    )

  describe "words", ->

    it "should return words which string contains", inject((wordsFilter) ->
      expect(wordsFilter("some str")).toEqual(["some", "str"])
      expect(wordsFilter("somestr")).toEqual(["somestr"])
    )

  describe "range", ->

    it "should return range of ints", inject((rangeFilter) ->
      expect(rangeFilter([], 7)).toEqual([0, 1, 2, 3, 4, 5, 6])
    )

  describe "format_date", ->

    it "should format date", inject((format_dateFilter) ->
      expect(format_dateFilter('')).toEqual('')
      expect(format_dateFilter('2013-10-09 11:50:00')).toEqual('09-10-2013 11:50')
    )

  describe "humanize_time", ->

    it "should humanize time duration description", inject((humanize_timeFilter) ->
      expect(humanize_timeFilter('')).toEqual('')
      expect(humanize_timeFilter(25)).toEqual('25 s')
      expect(humanize_timeFilter(60)).toEqual('1 m')
      expect(humanize_timeFilter(3600)).toEqual('1 h')
      expect(humanize_timeFilter(4000)).toEqual('1 h 6 m 40 s')
    )

  describe "bytes", ->

    it "should humanize bytes description", inject((bytesFilter) ->
      expect(bytesFilter(null)).toEqual('-')
      expect(bytesFilter(5)).toEqual('5.0 bytes')
      expect(bytesFilter(1000)).toEqual('1000.0 bytes')
      expect(bytesFilter(1024)).toEqual('1.0 kB')
      expect(bytesFilter(1000000)).toEqual('976.6 kB')
      expect(bytesFilter(1048576)).toEqual('1.0 MB')
    )
