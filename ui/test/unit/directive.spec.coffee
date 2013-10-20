'use strict'

# jasmine specs for directives go here
describe "directives", ->

  beforeEach(module "app.directives")

  describe "app-version", ->

    it "should print current version", ->
      module ($provide) ->
        $provide.value "version", "TEST_VER"
        return

      inject ($compile, $rootScope) ->
        element = $compile("<span app-version></span>")($rootScope)
        expect(element.text()).toEqual "TEST_VER"

  describe "json-editor", ->

    it "should create json editor control for object", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = {"str_param": "value"}

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<span class="jsonObjectKey">')
        expect(element.html()).toContain('<span ng-switch-default="" class="jsonLiteral ng-scope">')
        expect(element.html()).toContain('<input type="text" ng-model="val" placeholder="Empty" ng-model-onblur="" ng-change="item[key] = val" class="ng-pristine ng-valid">')
        expect(element.html()).toNotContain('<ol class="arrayOl ng-pristine ng-valid" ng-model="item">')

    it "should create json editor control for array", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = ["one", "two", "three"]

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<ol class="arrayOl ng-pristine ng-valid" ng-model="item">')

    it "should create json editor control for string", ->
      inject ($compile, $rootScope) ->
        $rootScope.jsonVal = "Some string"

        element = $compile('<div><json-editor item="jsonVal"></json-editor></div>')($rootScope)
        $rootScope.$digest()

        expect(element.html()).toContain('<span ng-switch-default class="jsonLiteral">')
        expect(element.html()).toNotContain('<span class="jsonObjectKey">')
        expect(element.html()).toNotContain('<ol class="arrayOl ng-pristine ng-valid" ng-model="item">')
