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

      @click: (datum, updateFn)->
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
            return "hsl(#{(1 - datum.item.impurity)*260 + 100}, 75%, 10%)"
          .attr("stroke-width", 1)
          .style "fill", (datum)->
            return "hsl(#{(1 - datum.item.impurity)*260 + 100}, 75%, 75%)"
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
        if node.item.rule
          newNode.text.push "#{node.item.rule}"
        if node.item.impurity
          newNode.text.push "Impurity: #{node.item.impurity}"
        if node.item.samples
          newNode.text.push "Samples: #{node.item.samples}"
        if node.item.values
          newNode.text.push "Values: [#{node.item.value.join(',')}]"
        return newNode


    return DecisionTreeUtils
  ])

.directive('cmlDecisionTree', [
    'DecisionTreeUtils'
    (DTUtils)->
      ###
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

          i = 0
          duration = 750
          rectW = 100
          rectH = 50
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
            svg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")

          setScale = (datum)->
            datum.scale = DTUtils.getScale @getBBox(), @parentNode.getBBox(), 2, 1

          tree = d3.layout.tree()
            .nodeSize([rectW + nodeHSep, rectH + nodeVSep])

          diagonal = d3.svg.diagonal()
            .projection (d)->
              return [d.x + rectW / 2, d.y + rectH / 2]

          zm = d3.behavior.zoom()
          .scaleExtent([1,3]).on("zoom", redraw)

          svg = d3.select(element[0]).append('svg')
#            .attr('width', width)
#            .attr('height', height)
            .call(zm).append('g')
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
            node = svg.selectAll('g.node')
              .data nodes, (d)->
                return d.id or (d.id = ++i)

            # Enter any new nodes at the parent's previous position.
            nodeEnter = node.enter().append('g')
              .attr('class', 'node')
              .attr 'transform', (datum)->
                return "translate(#{source.x0},#{source.y0})"
              .on 'click', (datum)->
                DTUtils.click(datum, updateTree)
            
            rect = nodeEnter.append('rect')
            DTUtils.updateRect(rect, rectW, rectH)

            fontSize = 10
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
            .each (datum)->
              bbox = @getBBox()
              parent = @parentNode.getBBox()

              dx = fontSize/2
              dy = fontSize/2 - (bbox.y - parent.y)

              translate = ''
              scale = ''
              if rectW - bbox.width >= fontSize and rectH - bbox.height >= fontSize
                dx = (rectW - bbox.width)/2
                dy = (rectH - bbox.height)/2 - (bbox.y - parent.y)
                translate = "translate(#{dx}, #{dy})"
              else
                min = Math.min(rectW/(bbox.width + fontSize), rectH/(bbox.height + fontSize))
                scale = "scale(#{min}, #{min})"
                dx = (rectW - bbox.width*min)/2
                dy = (rectH - bbox.height*min)/2 - (bbox.y*min - parent.y)
                translate = "translate(#{dx}, #{dy})"
              datum.transform = "#{translate} #{scale}"

            .attr 'transform', (datum)->
              return datum.transform

#              .style('fill-opacity', 1)
#              .attr('x', rectW / 2)
#              .attr('y', rectH / 2)
#              .attr('text-anchor', 'middle')
#              .style('font-size', '1px')
#              .each(setScale)
#              .style 'font-size', (datum) ->
#                return "#{datum.scale}px"

            # Transition nodes to their new position.
            nodeUpdate = node.transition()
              .duration(duration)
              . attr 'transform', (datum)->
                  return "translate(#{datum.x},#{datum.y})"
              
            rect = nodeUpdate.select('rect')
            DTUtils.updateRect(rect, rectW, rectH)

#            nodeUpdate.select('text')
#              .style('fill-opacity', 1)
#              .attr('x', rectW / 2)
#              .attr('y', rectH / 2)
#              .attr('text-anchor', 'middle')
#              .style('font-size', '1px')
#              .each(setScale)
#              .style 'font-size', (datum) ->
#                return "#{datum.scale}px"

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
            link = svg.selectAll('path.link')
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

          drawTree = (modelRoot)->
            # Compute the new tree layout.
            root = DTUtils.process(modelRoot)
            root.x0 = 0
            root.y0 = rectH / 2
            _.forEach root.children, DTUtils.collapse

            updateTree(root)

          scope.$watch attributes.root, (newVal)->
            if newVal
              drawTree newVal
      }
  ])