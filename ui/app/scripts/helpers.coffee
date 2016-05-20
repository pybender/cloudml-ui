'use strict'

### Helpers ###

angular.module('app.helpers', [])


# strftime for JavaScript

#   Field description (taken from http://tinyurl.com/65s2qw)

#    %a  Locale’s abbreviated weekday name.
#    %A  Locale’s full weekday name.
#    %b  Locale’s abbreviated month name.
#    %B  Locale’s full month name.
#    %c  Locale’s appropriate date and time representation.
#    %d  Day of the month as a decimal number [01,31].
#    %H  Hour (24-hour clock) as a decimal number [00,23].
#    %I  Hour (12-hour clock) as a decimal number [01,12].
#    %j  Day of the year as a decimal number [001,366].
#    %m  Month as a decimal number [01,12].
#    %M  Minute as a decimal number [00,59].
#    %p  Locale’s equivalent of either AM or PM.
#    %S  Second as a decimal number [00,61].
#    %U  Week number of the year (Sunday as the first day of the week) as a
#        decimal number [00,53]. All days in a new year preceding the first
#        Sunday are considered to be in week 0.
#    %w  Weekday as a decimal number [0(Sunday),6].
#    %W  Week number of the year (Monday as the first day of the week) as a
#        decimal number [00,53]. All days in a new year preceding the first
#        Monday are considered to be in week 0.
#    %x  Locale’s appropriate date representation.
#    %X  Locale’s appropriate time representation.
#    %y  Year without century as a decimal number [00,99].
#    %Y  Year with century as a decimal number.
#    %z  UTC time zone offset -HHMM or +HHMM.
#    %Z  Time zone name (no characters if no time zone exists).
#    %%  A literal '%' character.


days = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
    'Saturday'
]

months = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'
]

shortname = (name) ->
    return name.substr(0, 3);

zeropad = (n, size) ->
    n = '' + n
    size = size || 2
    while n.length < size
        n = '0' + n
    return n


twelve = (n) ->
    return if n <= 12 then n else n - 12

getWeekByMon = (d) ->
    mon = 1
    target  = new Date(d.valueOf())
    target.setHours(0, 0, 0, 0)
    jan1    = new Date(target.getFullYear(), 0, 1)
    dayDiff = (target-jan1) / 86400000 + 1

    if jan1.getDay() is mon
      return Math.ceil(dayDiff / 7)
    else
      mon = if jan1.getDay() is 0 then 2 else 9 - jan1.getDay()
      if dayDiff < mon
        return 0
      else
        monday = new Date(target.getFullYear(), 0, mon, 0, 0, 0, 0)
        dayDiff = (target - monday) / 86400000 + 1
        return Math.ceil(dayDiff / 7)

getWeekBySun = (d) ->
    sun = 0
    target  = new Date(d.valueOf())
    target.setHours(0, 0, 0, 0)
    jan1    = new Date(target.getFullYear(), 0, 1)
    dayDiff = (target-jan1) / 86400000 + 1

    if jan1.getDay() is sun
      return Math.ceil(dayDiff / 7)
    else
      sun = 8 - jan1.getDay()
      if dayDiff < sun
        return 0
      else
        sunday = new Date(target.getFullYear(), 0, sun, 0, 0, 0, 0)
        dayDiff = (target - sunday) / 86400000 + 1
        return Math.ceil(dayDiff / 7)

dayOfYear = (d) ->
    target = new Date(d.valueOf())
    jan1 = new Date(target.getFullYear(), 0, 1)
    day = Math.ceil((target-jan1) / 86400000)
    return day

tzOffset = (date) ->
    min = date.getTimezoneOffset()
    sign = if min < 0 then '-' else '+'
    hour = zeropad(Math.floor(Math.abs(min) / 60))
    mins = zeropad(Math.abs(min) % 60)
    return sign + hour + mins

tzName = (date) ->
    return date.toString().substr(date.toString().length - 4, 3)

strftime = (format, date) ->
    date = new Date(date)
    fields = {
        a: shortname(days[date.getDay()]),
        A: days[date.getDay()],
        b: shortname(months[date.getMonth()]),
        B: months[date.getMonth()],
        c: date.toString(),
        d: zeropad(date.getDate()),
        f: zeropad(date.getMilliseconds()*1000, 6),
        H: zeropad(date.getHours()),
        I: zeropad(twelve(date.getHours())),
        j: zeropad(dayOfYear(date),3),
        m: zeropad(date.getMonth() + 1),
        M: zeropad(date.getMinutes()),
        p: if date.getHours() >= 12 then 'PM' else 'AM',
        S: zeropad(date.getSeconds()),
        U: zeropad(getWeekBySun(date)),
        w: zeropad(date.getDay() + 1),
        W: zeropad(getWeekByMon(date)),
        x: date.toLocaleDateString(),
        X: date.toLocaleTimeString(),
        y: ('' + date.getFullYear()).substr(2, 4),
        Y: '' + date.getFullYear(),
        z: tzOffset(date),
        Z: tzName(date),
        '%' : '%'
    }

    result = ''
    i = 0
    while i < format.length
      if format[i] is '%'
        result = result + fields[format[i + 1]]
        i++
      else
        result = result + format[i]
      i++
    return result


strftimeDate = (pattern, unixdate) ->
    # use strftime because strptime will ignore some pattern pieces on backend
    # anyway, but every pattern will be available on frontend
    return strftime(pattern, unixdate*1000)
