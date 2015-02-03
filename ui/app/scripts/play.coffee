angular.module('app.play.controllers', ['app.config', ])

.controller('PlayCtrl', [
  '$scope'
  '$timeout'
  'Model'

  ($scope, $timeout, Model) ->
    $timeout ->
#      d3.selectAll("p")
#      .data([4, 8, 15, 16, 23, 42])
#      .style("font-size", (d) -> return d + "px" )

#      d3.select('body').selectAll("p")
#      .data([4, 8, 15, 16, 23, 42])
#      .enter().append("p")
#      .text((d) -> return "I’m number " + d + "!")

#      p = d3.select("body").selectAll("p")
#      .data([4, 8, 15, 16, 23, 42])
#      .text(String)
#
#      # Enter…
#      p.enter().append("p")
#      .text(String)
#
#      # Exit…
#      p.exit().remove()

      $scope.model = new Model({id: 65})
      $scope.model.$load {show: ['visualization_data']}
      .then ->
        diameter = 960
        rectWidth = 20
        rectHeight = 10
        graphWidth = 1000
        graphHeight = 1000

        data = $scope.model.visualization_data
        root = data.tree
        tree = d3.layout.tree()
        .size([1000, 1000])
        .children (d)->
          children = []
          if d.left?
            children.push d.left
          if d.right?
            children.push d.right
          return children
        .separation (da, db)->
          return if da.parent is db.parent then 100 else 200
        #.nodeSize([rectWidth, rectHeight])

        diagonal = d3.svg.diagonal() #.radial()
        #.projection((d) -> return [d.y, d.x / 180 * Math.PI] )

        svg = d3.select('svg')
          .attr('width', graphWidth)
          .attr('height', graphHeight)
        .append("g")
          .attr('transform', 'translate(0,' + 50 + ')')

        nodes = tree.nodes(root)
        links = tree.links(nodes)
        console.log 'nodes was', nodes
        console.log 'links was', links

        link = svg.selectAll(".link")
        .data(links)
        .enter().append("path")
        .attr("class", "link")
        .attr("d", diagonal);

        node = svg.selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node")

        node.append("rect")
        .attr('x', (d)-> d.x - rectWidth/2)
        .attr('y', (d)-> d.y - rectHeight/2)
        .attr('width', rectWidth)
        .attr('height', rectWidth)

        node.append("text")
        .attr("dy", ".31em")
        .attr("text-anchor", "start")
        #.attr("transform", (d) -> return d.x < 180 ? "translate(8)" : "rotate(180)translate(-8)" )
        .text((d) -> return d.item.rule)

        console.log 'nodes was', nodes
        console.log 'links was', links
      , (err)->
        console.log 'something went wrong'
])

