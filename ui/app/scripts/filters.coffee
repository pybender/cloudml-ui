'use strict'

### Filters ###

angular.module('app.filters', [])

.filter('interpolate', [
  'version',

(version) ->
  (text) ->
    String(text).replace(/\%VERSION\%/mg, version)
])

.filter('capfirst', [() ->
  (text) ->
    t = String(text)
    return t[0].toUpperCase() + t.slice(1)
])

.filter('words', [() ->
  (text) ->
    t = String(text)
    return t.split(/\W+/)
])

.filter('range', [() ->
  (input, total) ->
    total = parseInt(total)
    for num in [0..total - 1]
      input.push(num)
    return input
])


.filter('format_date', [() ->
  (text) ->
    dt = new Date(text)
    d = add_zero(dt.getDate())
    m = add_zero(dt.getMonth() + 1)
    y = dt.getFullYear()
    h = add_zero(dt.getHours())
    mm = add_zero(dt.getMinutes())
    return d + "-" + m + "-" + y + ' ' + h + ':' + mm
])

add_zero = (val) ->
  if val < 10
    val = '0' + val
  return val
