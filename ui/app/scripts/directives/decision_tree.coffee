angular.module('app.directives')

.factory('DecisionTreeUtils', [->
    ###
    A collection of decision tree utilities exposed as factory for easy testing
    ###
    class DecisionTreeUtils

      @getScale: (datumBBox, parentBBox, hMargin, vMargin) ->
        ###
        Gets the proper scale from the datum bounding box and parent's bounding
        box with hMargin as horizontal margin in pixels and vMargin as vertical
        margin in pixels
        ###
        return Math.min(parentBBox.width/(datumBBox.width + hMargin), parentBBox.height/(datumBBox.height + vMargin))

      @getTextTransform: (node, rectW, rectH, fontSize)->
        ###
        Gets a transform string for <text> node containing multiple tspan such
        that the text centered and doesn't cross the bounding box of the rect
        ###
        return ""
        bbox = node.getBBox()
        parentBBox = node.parentNode.getBBox()
        dx = fontSize/2
        dy = fontSize/2 - (bbox.y - parentBBox.y)

        translate = ''
        scale = ''
        if rectW - bbox.width >= fontSize and rectH - bbox.height >= fontSize
          dx = (rectW - bbox.width)/2
          dy = (rectH - bbox.height)/2 - (bbox.y - parentBBox.y)
          translate = "translate(#{dx}, #{dy})"
        else
          min = Math.min(rectW/(bbox.width + fontSize), rectH/(bbox.height + fontSize))
          scale = "scale(#{min}, #{min})"
          dx = (rectW - bbox.width*min)/2
          dy = (rectH - bbox.height*min)/2 - (bbox.y*min - parentBBox.y)
          translate = "translate(#{dx}, #{dy})"
        return "#{translate} #{scale}"


      @click: (node, datum, updateFn)->
        ###
        On clicking a datum it will collapse or expands children based on initial
        state by swapping children with _children and resetting _children or
        children
        ###
        if datum.children
          datum._children = datum.children
          datum.children = null
        else
          datum.children = datum._children
          datum._children = null
        updateFn(datum)

      @collapse: (datum)->
        ###
        Collapses a datum and all its children. This is similar to click
        above but will override children state and make them all collapsed
        ###
        if datum.children
          datum._children = datum.children
          _.forEach datum._children, DecisionTreeUtils.collapse
          datum.children = null

      @updateRect: (rect, rectWidth, rectHeight)->
        rect
          .attr("width", rectWidth)
          .attr("height", rectHeight)
          .attr "stroke", (datum)->
            return "hsl(#{datum.impurity*260 + 100}, 75%, 10%)"
          .attr("stroke-width", 1)
          .style "fill", (datum)->
            return "hsl(#{datum.impurity*260 + 100}, 75%, 75%)"
        return rect


      @process: (node)->
        ###
        returns a new tree structure compatible with d3
        changes
        ###
        newNode = _.omit(node, ['id'])
        newNode.children = []
        if node.children
          for child in node.children
            newNode.children.push(DecisionTreeUtils.process(child))
        newNode.text = []
        if node.name
          name = node.name
          newNode.title = name
          if node.name.length > 15
            name = node.name.substring(0, 15) + "..."
            newNode.title = node.name
          newNode.text.push "#{name}"
        if typeof node.impurity isnt undefined
          newNode.text.push "Impurity: #{node.impurity}"
        if node.samples
          newNode.text.push "Samples: #{node.samples}"
        if node.value
          newNode.title = "Value: [#{node.value.join(',')}]"
          newNode.text.push "Value: [#{node.value.join(',')}]"
        return newNode


    return DecisionTreeUtils
  ])

.directive('cmlDecisionTree', [
    '$timeout'
    'DecisionTreeUtils'
    ($timeout, DTUtils)->
      ###
      adapted from
        http://jsfiddle.net/nadersoliman/5ptb17bz/
        http://jsfiddle.net/augburto/YMa2y/
      Directive to draw a decision tree using pure d3.
      Assumes a binary tree, where each node has left and right children or none
      Expects a root of the tree in the form
      item:
        samples: 1000
        id: "0"
        rule: "opening->budget"
        impurity: 0.5716
        right: {right child node}
        left: {left child node}
      ###

      return {
        restrict: 'E'
        template: ''
        link: (scope, element, attributes) ->
          nodes = null
          links = null
          root = null
          treeNode = null
          svg = null

          i = 0
          duration = 500
          rectW = 100
          rectH = 60
          fontSize = 12
          nodeHSep = 5
          nodeVSep = 5
          # margin =
          #   top: 20
          #   right: 20
          #   bottom: 20
          #   left: 20
          #width = 1560 - margin.right - margin.left
          #height = 800 - margin.top - margin.bottom

          redraw = ->
            treeNode.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")

          tree = d3.layout.tree()
            .nodeSize([rectW + nodeHSep, rectH + nodeVSep])

          diagonal = d3.svg.diagonal()
            .projection (d)->
              return [d.x + rectW / 2, d.y + rectH / 2]

          zm = d3.behavior.zoom()
          .scaleExtent([-3, 3]).on("zoom", redraw)

          svg = d3.select(element[0]).append('svg')
            .call(zm)

          treeNode = svg.append('g')

          resizeWindow = () ->
            width = window.innerWidth - 200
            if width < 500 then width = 500
            svg.attr("width", width)
            treeNode.attr('transform', 'translate('+ width / 2 +',20)')
            # necessary so that zoom knows where to zoom and unzoom from
            zm.translate([width / 2, 20])

          window.onresize = resizeWindow
          resizeWindow()

          updateTree = (source)->
            nodes = tree.nodes(root).reverse()
            links = tree.links(nodes)

            # Normalize for fixed-depth.
            _.forEach nodes, (datum)->
              datum.y = datum.depth * 70

            # Update the nodes
            node = treeNode.selectAll('g.node')
              .data nodes, (d)->
                return d.id or (d.id = ++i)

            # Enter any new nodes at the parent's previous position.
            nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr 'transform', (datum)->
                return "translate(#{source.x0},#{source.y0})"
            .on 'click', (datum)->
              DTUtils.click(d3.select(@), datum, updateTree)
            .style 'cursor', (datum)->
              if datum.children?.length > 0 or datum._children?.length > 0
                return 'pointer'
              else
                return 'default'
#            .on 'mouseenter', (datum)->
#              clientBBox = @getBoundingClientRect()
#              toolTip = ''
#              for t, i in datum.text
#                toolTip = "#{toolTip}<p #{if i is 0 then "class='bold'" else ""}>#{t}</p>"
#              nv.tooltip.show([clientBBox.right, clientBBox.top], toolTip)
#            .on 'mouseleave', (datum)->
#              nv.tooltip.cleanup()

            nodeEnter.append('title')
            .text (datum)->
              return datum.title

            nodeEnter.append('rect')
              .each ->
                DTUtils.updateRect(d3.select(@), rectW, rectH)

            # creating tspan children of the text node, fixing their fontsize
            # we are going to scale later
            textNode = nodeEnter.append('text')
            textNode
              .selectAll('tspan')
                .data (datum)->
                  return datum.text
                .enter().append('tspan')
                .attr 'font-size', "#{fontSize}px"
                .text (d)->
                  return d
                .attr 'y', (d, idx)->
                  return (idx + 1)*(fontSize + 2)
                .attr 'x', 0

            textNode
              .attr 'transform', (datum)->
                return DTUtils.getTextTransform(@, rectW, rectH, fontSize)

            # Transition nodes to their new position.
            nodeUpdate = node.transition()
              .duration(duration)
              . attr 'transform', (datum)->
                  return "translate(#{datum.x},#{datum.y})"
              
            nodeUpdate.select('rect')
              .each ->
                DTUtils.updateRect(d3.select(@), rectW, rectH)

            # Transition exiting nodes to the parent's new position.
            nodeExit = node.exit().transition()
              .duration(duration)
              .attr 'transform', (datum)->
                return "translate(#{source.x},#{source.y})"
              .remove()
            
            nodeExit.select('rect')
              .attr('width', rectW)
              .attr('height', rectH)
              .attr('stroke', 'black')
              .attr('stroke-width', 1)
  
            nodeExit.select('text')
            
            # Update the links
            link = treeNode.selectAll('path.link')
              .data links, (datum)->
                return datum.target.id

            # Enter any new links at the parent's previous position.
            link.enter().insert('path', 'g')
              .attr('class', 'link')
              .attr('x', rectW / 2)
              .attr('y', rectH / 2)
              .attr 'd', (datum) ->
                o =
                  x: source.x0
                  y: source.y0
                return diagonal({source: o, target: o})
  
            # Transition links to their new position.
            link.transition()
              .duration(duration)
              .attr('d', diagonal)
  
            # Transition exiting nodes to the parent's new position.
            link.exit().transition()
              .duration(duration)
              .attr 'd', (datum)->
                o =
                  x: source.x,
                  y: source.y
                return diagonal({source: o, target: o})
              .remove()
  
            # Stash the old positions for transition.
            _.forEach nodes, (datum)->
              datum.x0 = datum.x
              datum.y0 = datum.y
              return
              
          drawLegend = ->
            idGradient = 'theGradient'
            
            gNode = svg.append('g')
              .attr('x', 0)
              .attr('y', 0)
              .attr('width', 60)
              .attr('height', 200)
              .attr('transform', 'translate(0, 20)')

            gNode.append('defs')
              .append('linearGradient')
                .attr('id', idGradient)
                .attr('x1', '0%')
                .attr('x2', '0%')
                .attr('y1', '0%')
                .attr('y2', '100%')
                .selectAll('stop')
                  .data ->
                    numberHues = 100
                    hueStart = 100
                    hueEnd = 360
                    deltaPercent = 1/(numberHues-1)
                    deltaHue = (hueEnd - hueStart)/(numberHues - 1)

                    theData = []
                    for i in [0..numberHues]
                      theHue = hueStart + deltaHue*i
                      # the second parameter, set to 1 here, is the saturation
                      # the third parameter is "lightness"
                      rgbString = d3.hsl(theHue,0.75,0.75).toString()
                      p = 0 + deltaPercent*i
                      #console.log("i, values: " + i + ", " + rgbString + ", " + opacity + ", " + p);
                      theData.push({"rgb":rgbString, "opacity": 1, "percent": p})

                    return theData
                  .enter().append('stop')
                    .attr 'offset', (d)->
                      return d.percent
                    .attr 'stop-color',(d)->
                      return d.rgb

            gNode.append('rect')
              .attr('x', 30)
              .attr('y', 0)
              .attr('width', 20)
              .attr('height', 200)
              .attr('fill','url(#' + idGradient + ')')

            gNode.append('text')
              .attr('x', 10)
              .attr('y', 10)
              .style('font-size', '10px')
              .text('0%')

            gNode.append('text')
              .attr('x', 0)
              .attr('y', 200)
              .style('font-size', '10px')
              .text('100%')

            gNode.append('text')
            .attr('x', 70)
            .attr('y', 150)
            .style('font-size', '20px')
            .text('impurity')
            .attr('transform', 'rotate(-90, 70, 150)')


          drawTree = (modelRoot)->
            # Compute the new tree layout.
            root = DTUtils.process(modelRoot)
            root.x0 = 0
            root.y0 = rectH / 2
            #_.forEach root.children, DTUtils.collapse

            updateTree(root)
            drawLegend()

          scope.$watch attributes.root, (newVal)->
            if newVal
              # We have to wait for ng-show to kick in for proper calculation
              # of boudning boxes and positition of text inside the nodes
              $timeout ->
                drawTree newVal
              , 100
      }
  ])

.directive("cmlDecisionTextTreeOld", [
  'RecursionHelper'

  (RecursionHelper) ->
    return {
          restrict: "E",
          scope: {root: '='}
          templateUrl:'partials/directives/decision_text_tree.html'
          compile: (element) ->
              # // Use the compile function from the RecursionHelper,
              # // And return the linking function(s) which it returns
              return RecursionHelper.compile(element)
    }
])

.directive("cmlDecisionTextTree", [
    ()->
      return {
        restrict: 'E'
        scope: {root: '='}
        link: (scope, element, attributes) ->
          root = scope.root

          buildTree = (node, element) ->
            el = $("<ul></ul>")
            $(el).append($("<li></li>"))
            li = $(el).find("li")
            $(li).append($("<div></div>"))
            $(el).find("div").append($("<h5></h5>"))
            h5 = $(el).find("h5")

            l_class = ''
            if node.type == 'yes'
              l_class = 'label-success'
            if node.type == 'no'
              l_class = 'label-important'
            label = $("<span></span>")
            $(label).attr("class", " label "+l_class).text(node.type)

            if node.id != 0
              $(h5).append(label)

            if node.node_type == 'branch'
              name = $("<span></span>")
              $(name).text(' '+node.name+' ')
              $(h5).append(name)

            samples = $("<small></small>")
            $(samples).text(' ('+node.samples+' samples)')
            $(h5).append(samples)

            impurity_html = 'impurity: <span class="value">'+node.impurity+'</span>'
            if node.node_type == 'leaf'
              impurity_html += '<br/>value: <span class="value">'+node.value+'</span>'

            impurity = $("<small></small>")
            $(impurity).html(impurity_html)
            $(el).find("div").append(impurity)

            $(element).append(el)

            if node.children?
              for child in node.children
                buildTree(child, li)

          buildTree(root, element)
  }
])

.directive("swtDecisionTree", [

  () ->
    return {
          restrict: "E",
          scope: {root: '=', mode: '='}
          templateUrl:'partials/directives/decision_switch_tree.html'
    }
])