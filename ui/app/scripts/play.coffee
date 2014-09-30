angular.module('app.play.controllers', ['app.config', ])

.controller('PlayCtrl', [
  '$scope'
  '$timeout'

  ($scope, $timeout) ->
    $scope.availableColors = [{id:1, name:'Red'}, {id:2, name:'Green'},
      {id:3, name:'Blue'},{id:4, name:'Yellow'}, {id:5, name:'Magenta'},
      {id:6, name:'Maroon'}, {id:7, name:'Umbra'}, {id:8, name:'Turquoise'}]


    $scope.multipleDemo = {};
    $scope.multipleDemo.colors = [$scope.availableColors[0], $scope.availableColors[1]]

    $scope.multipleDemo.select2Colors = [1, 2]


    $scope.$watch 'multipleDemo.tags', (newVal, oldVal)->
      if newVal
        $scope.modelTags = $scope.multipleDemo.tags #(tag.id for tag in $scope.multipleDemo.tags)

    $scope.$watch 'modelTags', (newVal, oldVal)->
      console.log 'newVal:', newVal, 'oldVal:', oldVal
      if angular.isString(newVal)
        console.log 'converting'
        ids = newVal.split(',')
        $scope.modelTags = (tag for tag in $scope.tag_list when tag.id + '' in ids)


    $scope.select2params = {
      multiple: true
      query: (query) ->
        data = {results: angular.copy $scope.tag_list}
        query.callback(data)

      createSearchChoice: (term, data) ->
        cmp = () ->
          return this.text.localeCompare(term) == 0
        if $(data).filter(cmp).length == 0 then return {id: term, text: term}
    }

    $timeout ->
      $scope.multipleDemo.tags = [{id: 1, text: 'Tag1'}, {id: 2, text: 'Tag2'}]
    , 100

    $timeout ->
      $scope.tag_list = [{id: 1, text: 'Tag1'}, {id: 2, text: 'Tag2'},
        {id: 3, text: 'Tag3'}, {id: 4, text: 'Tag14'}]
    , 200

])
