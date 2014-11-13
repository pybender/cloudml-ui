# Adapted from https://github.com/novus/nvd3/issues/367
# to fix TypeError: 'undefined' is not a function (evaluating 'nv.utils.optionsFunc.bind(chart)')
if not Function.prototype.bin
  Function.prototype.bind = (oThis) ->
    if typeof @ isnt  'function'
      # closest thing possible to the ECMAScript 5
      # internal IsCallable function
      throw "TypeError : Function.prototype.bind - what is trying to be bound is not callable"

    aArgs = Array.prototype.slice.call(arguments, 1)
    fToBind = this
    fNOP = ->
    fBound = ->
      target = if @ instanceof fNOP and oThis then @ else oThis
      return fToBind.apply target, aArgs.concat(Array.prototype.slice.call(arguments))

    fNOP.prototype = @prototype
    fBound.prototype = new fNOP

    return fBound
