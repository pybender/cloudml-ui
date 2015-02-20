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
            return "hsl(#{datum.item.impurity*260 + 100}, 75%, 10%)"
          .attr("stroke-width", 1)
          .style "fill", (datum)->
            return "hsl(#{datum.item.impurity*260 + 100}, 75%, 75%)"
        return rect


      @process: (node)->
        ###
        returns a new tree structure compatible with d3
        changes
        item:
          samples: 1000
          id: "0"
          rule: "opening->budget"
          impurity: 0.5716
          right: {right child node}
          left: {left child node}
        to
        item:
          samples: 1000
          id: i
          org_id: '0'
          rule: "opening->budget"
          impurity: 0.5716
          children: [{left child node}, {right child node}]
        ###
        #console.log 'got node', node
        newNode = _.omit(node, ['id'])
        newNode.children = []
        if node.left
          newNode.children.push(DecisionTreeUtils.process(node.left))
        if node.right
          newNode.children.push(DecisionTreeUtils.process(node.right))
        #console.log 'got newNode', newNode
        newNode.text = []
        if node.item.name
          newNode.text.push "#{node.item.name}"
        else if node.item.rule
          newNode.text.push "#{node.item.rule}"
        if typeof node.item.impurity isnt undefined
          newNode.text.push "Impurity: #{node.item.impurity}"
        if node.item.samples
          newNode.text.push "Samples: #{node.item.samples}"
        if node.item.value
          newNode.text.push "Value: [#{node.item.value.join(',')}]"
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
          duration = 750
          rectW = 100
          rectH = 50
          fontSize = 10
          nodeHSep = 10
          nodeVSep = 10
#          margin =
#            top: 20
#            right: 120
#            bottom: 20
#            left: 120
#          width = 960 - margin.right - margin.left
#          height = 800 - margin.top - margin.bottom

          redraw = ->
            treeNode.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")

          tree = d3.layout.tree()
            .nodeSize([rectW + nodeHSep, rectH + nodeVSep])

          diagonal = d3.svg.diagonal()
            .projection (d)->
              return [d.x + rectW / 2, d.y + rectH / 2]

          zm = d3.behavior.zoom()
          .scaleExtent([1,3]).on("zoom", redraw)

          svg = d3.select(element[0]).append('svg')
            .call(zm)
            .attr('transform', 'translate(350,20)')
          treeNode = svg.append('g')
            .attr('transform', 'translate(350,20)')

          # necessary so that zoom knows where to zoom and unzoom from
          zm.translate([350, 20])

          updateTree = (source)->
            nodes = tree.nodes(root).reverse()
            links = tree.links(nodes)

            # Normalize for fixed-depth.
            _.forEach nodes, (datum)->
              datum.y = datum.depth * 180

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
              return datum.text.join(', ')

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
            _.forEach root.children, DTUtils.collapse

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