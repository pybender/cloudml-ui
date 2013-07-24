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

.filter('bytes', [() ->
  (bytes, precision) ->
    bytes = parseFloat(bytes)
    if isNaN(bytes) or not isFinite(bytes) or not bytes
      return '-'
    if not precision?
      precision = 1
    units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']
    number = Math.floor(Math.log(bytes) / Math.log(1024))
    console.log('Bytes: ' + bytes)
    console.log('Number: ' + number)
    rounded = (bytes / Math.pow(1024, Math.floor(number)))
    console.log('rounded: ' + rounded)
    return rounded.toFixed(precision) +  ' ' + units[number]
])

add_zero = (val) ->
  if val < 10
    val = '0' + val
  return val
