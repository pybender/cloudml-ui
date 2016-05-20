angular.module('app.directives')

.directive('fieldsMapper', [ ->
    return {
    restrict: 'E'
    require: 'ngModel'
    templateUrl: 'partials/directives/fields_mapper.html'
    replace: false
    scope: {
      params: '='
      value: '=ngModel'
      fields: '='
      name: '='
      disabled: '='
    }
    link: ($scope, element, attributes, ngModel) ->
      $scope.fieldsMap = {}

      $scope.$watch 'params', (nVal, oVal) ->
        if nVal != oVal
          $scope.resetFieldsMap()

      $scope.$watch 'fields', (nVal, oVal) ->
        if nVal != oVal
          $scope.resetFieldsMap()

      $scope.$watch 'disabled', (nVal, oVal) ->
        if nVal
          $scope.importParam = undefined
          $scope.dataField = undefined

      $scope.appendFieldMap = (importParam, dataField) ->
        if not importParam? or not dataField?
          return
        $scope.fieldsMap[importParam] = dataField
        index = $scope.params.indexOf(importParam)
        if index >= 0
          $scope.params.splice(index, 1)
        $scope.importParam = undefined
        $scope.dataField = undefined
        $scope.value = $scope.getVerificationParamsMap()

      $scope.removeField = (param) ->
        delete $scope.fieldsMap[param]
        $scope.params.push param
        $scope.value = $scope.getVerificationParamsMap()

      $scope.getVerificationParamsMap = () ->
        angular.toJson($scope.fieldsMap)

      $scope.resetFieldsMap = () ->
        $scope.fieldsMap = {}
        $scope.value = $scope.getVerificationParamsMap()
        #$scope.importParam = undefined
        #$scope.dataField = undefined

  }
])
