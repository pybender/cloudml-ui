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
    if not text
      return ''
    dt = moment(text, 'YYYY-MM-DD HH:mm:ss.SSS')
    if dt
      return dt.format('DD-MM-YYYY HH:mm')
    else
      return text
])

.filter('humanize_time', [() ->
  (text) ->
    if not text
      return ''
    dn = moment.duration(parseInt(text), 'seconds')
    if dn
      pieces = []
      if dn.hours()
        pieces.push(dn.hours() + ' h')
      if dn.minutes()
        pieces.push(dn.minutes() + ' m')
      if dn.seconds()
        pieces.push(dn.seconds() + ' s')
      return pieces.join(' ')
    else
      return text
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
    rounded = (bytes / Math.pow(1024, Math.floor(number)))
    return rounded.toFixed(precision) +  ' ' + units[number]
])

.filter("asDate", () ->
  return (input) ->
    return new Date(input))

.filter('true_false', () ->
    return (text, length, end) ->
        if (text) then return 'Yes'
        return 'No'
)

add_zero = (val) ->
  if val < 10
    val = '0' + val
  return val
