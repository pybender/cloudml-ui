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
    }
    link: ($scope, element, attributes, ngModel) ->
      $scope.fieldsMap = {}

      $scope.appendFieldMap = (importParam, dataField) ->
        if not importParam? or not dataField?
          return
        $scope.fieldsMap[importParam] = dataField
        $scope.params.pop importParam
        $scope.importParam = undefined
        $scope.dataField = undefined
        $scope.value = $scope.getVerificationParamsMap()

      $scope.removeField = (param) ->
        delete $scope.fieldsMap[param]
        $scope.params.push param
        $scope.value = $scope.getVerificationParamsMap()

      $scope.getVerificationParamsMap = () ->
        angular.toJson($scope.fieldsMap)
  }
])
