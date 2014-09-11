'use strict'

# jasmine specs for directives go here
describe "directives", ->

  $compile = null
  $rootScope = null
  $scope = null
  $provide = null
  $httpBackend = null
  $window = null

  beforeEach ->
    module 'ngCookies'
    module 'ngRoute'
    module 'ui.bootstrap'

    module 'app.base'
    module "app.directives"
    module 'app.models.model'
    module 'app.importhandlers.model'
    module 'app.xml_importhandlers.models'
    module 'app.datasets.model'
    module 'app.features.models'
    module 'app.templates' # to serve partials html
    module 'app.filters'

    module 'app.services', ($provide) ->
      $provide.value "version", "TEST_VER"
      return

    inject ($injector) ->
      $rootScope = $injector.get('$rootScope')
      $compile = $injector.get('$compile')
      $scope = $rootScope.$new()
      $httpBackend = $injector.get('$httpBackend')
      $window = $injector.get('$window')
      $window.alert = jasmine.createSpy '$window.alert'
      $window.confirm = jasmine.createSpy('$window.confirm')

  describe "app-version", ->

    it "should print current version", ->
      element = $compile("<span app-version></span>")($scope)
      expect(element.text()).toEqual "TEST_VER"

  describe 'editable', ->

    elem = null
    editableOpts = null
    beforeEach ->
      elem = null
      editableOpts = null
    afterEach ->
      elem.remove()

    afterEach ->
      $httpBackend.verifyNoOutstandingExpectation()
      $httpBackend.verifyNoOutstandingRequest()

    prepareContext = (inputTypeText=true)->
      if inputTypeText
        html = """
<span ng-bind="instance.name || 'instance name here'"
editable="instance" value="instance.name" editable-field="name" editable-input="text"
editable-placement="right"></span>
"""
      else
        html = """
<span ng-bind="instance.obj.name || 'instance name here'"
editable="instance" value="instance.obj.id" editable-field="obj" editable-input="select" source="instance.objects"
editable-placement="right" display="instance.obj.name"></span>
"""
      elem = $compile(html)($scope)
      $(document.body).append(elem)
      $scope.$digest()
      editableOpts = elem.data('editable').options

      expect(editableOpts.autotext).toEqual 'never'
      expect(editableOpts.placement).toEqual 'right'
      if inputTypeText
        expect(editableOpts.type).toEqual 'text'
        expect(editableOpts.source).toBeUndefined()
      else
        expect(editableOpts.type).toEqual 'select'
        expect(editableOpts.source).toEqual jasmine.any(Function)


    simulateXeditableSubmit = ->
      editableOpts.success editableOpts.url({value: $scope.instance.name})

    it 'should throw exception if object doesnt have $save fn', ->
      $scope.instance = {}

      prepareContext()

      expect(->
        editableOpts.url()
      ).toThrow new Error "Editable: can't handle object without $save method"

    it 'should $save with suuccess', inject (Model)->
      model = new Model
        id:123
        name: 'zinger'
      $scope.instance = model

      prepareContext()

      # respond to value changes
      $scope.instance.name = 'zinger_again'
      $scope.$digest()
      # simulate a submit
      updatedModel = new Model
        id: 123
        name: 'zinger_again'
      response = {}
      response[model.API_FIELDNAME] = updatedModel
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/"
      .respond 200, angular.toJson(response)
      # doing what x-editable would be doing
      simulateXeditableSubmit()
      $httpBackend.flush()
      expect($scope.instance.name).toEqual 'zinger_again'

    it 'should revert back on save failure', inject (Model)->
      model = new Model
        id:123
        name: 'zinger'
      $scope.instance = model

      prepareContext()

      $scope.instance.name = 'failed_zinger'
      $scope.$digest()
      # simulate a submit
      updatedModel = new Model
        id: 123
        name: 'zinger'
      response = {}
      response[model.API_FIELDNAME] = updatedModel
      $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/"
      .respond 400
      # doing what x-editable would be doing
      simulateXeditableSubmit()
      $httpBackend.flush()
      expect($scope.instance.name).toEqual 'zinger'

    it 'should handle select type, along with observing display attribute, properly handling errors',
      inject (Model)->
        [obj1, obj2, obj3] = [
          {id:1, name: 'one'}, {id:2, name: 'two'}, {id:3, name: 'three'}]
        model = new Model
          id:123
          obj: obj1
        $scope.objects = [obj1, obj2, obj3]
        $scope.instance = model

        prepareContext(false)
        model.obj = obj2
        $scope.$digest()
        expect($(elem).text()).toEqual 'two'

        # simulate a submit
        $httpBackend.expectPUT "#{model.BASE_API_URL}#{model.id}/"
        .respond 400
        # doing what x-editable would be doing
        simulateXeditableSubmit()
        # upon the following flush, the watch is called with newVal undefined
        # I don't know why, this screws up everything afterwords, as
        $httpBackend.flush()
        # TODO: nader20140910 following line should be the case,
        # look in the comments of directives.coffee#editable directive
        # for xdescription of the bug
        #expect($(elem).text()).toEqual 'one'


  describe 'weightsTable', ->

    elem = null
    html = null

    beforeEach ->
      elem = null
      html = null

    prepareContext = (weights) ->
      $scope.someWeights = weights
      elem = $compile(
        '<weights-table weights="someWeights"></weights-table>')($scope)
      $scope.$digest()
      html = $(elem).html()

    checkHtml = ->
      if $scope.someWeights
        for weight in $scope.someWeights
          for key, val of weight
            if key is '$$hashKey'
              continue
            expect(html).toContain val

    it 'should render weights table', ->

      someWeights = [{segment_id: 1, name: 'segment1', css_class: 'css_class1',
      value: 'value1'} , {segment_id: 2, name: 'segment2', css_class: 'css_class2', value: 'value2'}]
      prepareContext someWeights
      checkHtml()

    it 'should respond to weights changes', ->

      prepareContext null
      checkHtml()

      $scope.someWeights = [{segment_id: 1, name: 'segment1', css_class: 'css_class1', value: 'value1'}]
      $scope.$digest()
      html = $(elem).html()
      checkHtml()

        # change a weight
      $scope.someWeights[0].name = 'zinger'
      $scope.$digest()
      html = $(elem).html()
      checkHtml()

      # add a weight
      $scope.someWeights.push {segment_id: 3, name: 'segment3', css_class: 'css_class3', value: 'value3'}
      $scope.$digest()
      html = $(elem).html()
      checkHtml()

  describe 'goToDocs', ->
    elem = null
    html = null

    beforeEach ->
      elem = null
      html = null

    prepareContext = (page, section=undefined, title=undefined) ->
      sectionAttr = if section then "section='#{section}'" else ''
      titleAttr = if title then "title='#{title}'" else ''
      elem = $compile("<go-to-docs page='#{page}' #{sectionAttr} #{titleAttr}>")($scope)
      $scope.$digest()
      html = elem[0].outerHTML

    it 'should render go to docs', ->
      prepareContext 'the_page', 'the_section', 'the_title'

      expect(html).toContain 'http://cloudml.int.odesk.com/docs/the_page.html#the_section'
      expect(html).toContain 'the_title'

      prepareContext 'the_page'

      expect(html).toContain 'http://cloudml.int.odesk.com/docs/the_page.html#'
      expect(html).toContain 'click and read the docs for more info'


  describe 'weightedDataParameters', ->

    elem = null
    html = null

    beforeEach ->
      elem = null
      html = null

    afterEach ->
      elem.remove()

    prepareContext = (value) ->
      $scope.someValue = value
      elem = $compile('<weighted-data-parameters val="someValue" />')($scope)
      $(document.body).append(elem)
      $scope.$digest()

    it 'should render a weight', ->

      prepareContext {weight: 'some_weight', css_class: 'some_css', value: 'some_value'}
      spanElem = $('>span', elem)
      divElem = $('>div', elem)
      spanHtml = spanElem[0].outerHTML
      expect(spanElem.css('display')).toEqual 'inline'
      expect(divElem.css('display')).toEqual 'none'
      expect(spanHtml).toContain 'some_weight'
      expect(spanHtml).toContain 'some_css'
      expect(spanHtml).toContain 'some_value'

    it 'should render weights of type list ', ->

      val = {type: 'List', value: ['WORD1', 'WORD2', 'WORD3'],
      weights:
        word1: {weight: 'some_weight1', css_class: 'some_css1'}
        word2: {weight: 'some_weight2', css_class: 'some_css2', value: 'some_value2'}
        word3: {css_class: 'some_css3'}
      }
      prepareContext val
      spanElem = $('>span', elem)
      divElem = $('>div', elem)
      listSpan = $('>span:eq(0)', divElem)
      dictSpan = $('>span:eq(1)', divElem)
      word1ListSpan = $('>span:eq(0)', listSpan)
      word2ListSpan = $('>span:eq(1)', listSpan)
      word3ListSpan = $('>span:eq(2)', listSpan)

      expect(spanElem.css('display')).toEqual 'none'
      expect(listSpan.css('display')).toEqual 'inline'
      expect(dictSpan.css('display')).toEqual 'none'

      expect($('>span:eq(0)', word1ListSpan).css('display')).toEqual 'inline'
      expect($('>span:eq(1)', word1ListSpan).css('display')).toEqual 'none'
      expect($('>span:eq(0)', word2ListSpan).css('display')).toEqual 'inline'
      expect($('>span:eq(1)', word2ListSpan).css('display')).toEqual 'none'
      expect($('>span:eq(0)', word3ListSpan).css('display')).toEqual 'none'
      expect($('>span:eq(1)', word3ListSpan).css('display')).toEqual 'inline'

      listHmlt = listSpan[0].outerHTML
      for v in val.value
        expect(listHmlt).toContain v
      for v in ['some_css1', 'some_css2']
        expect(listHmlt).toContain "badge #{v}"
      for v in ['some_weight1', 'some_weight2']
        expect(listHmlt).toContain "weight=#{v}"


    it 'should render weights of type dict ', ->

      val = {type: 'Dictionary',
      weights:
        dictword1: {weight: 'some_dict_weight1', css_class: 'some_dict_css1'}
        dictword2: {weight: 'some_dict_weight2', css_class: 'some_dict_css2', value: 'some_dict_value2'}
        dictword3: {css_class: 'some_dict_css3'}
      }
      prepareContext val
      spanElem = $('>span', elem)
      divElem = $('>div', elem)
      listSpan = $('>span:eq(0)', divElem)
      dictSpan = $('>span:eq(1)', divElem)

      expect(spanElem.css('display')).toEqual 'none'
      expect(listSpan.css('display')).toEqual 'none'
      expect(dictSpan.css('display')).toEqual 'inline'

      dictHtml = dictSpan[0].outerHTML
      for key, value in val.weights
        expect(dictHtml).toContain value.weight
      for v in ['some_dict_css1', 'some_dict_css2']
        expect(dictHtml).toContain "badge #{v}"
      for v in ['some_dict_weight1', 'some_dict_weight2']
        expect(dictHtml).toContain "weight=#{v}"


  describe 'confusionMatrix', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should render the confusion matrix', ->
      $scope.matrix = [
        ['head1', [999, 888]]
        ['head2', [777, 666]]
      ]
      $scope.url = 'some/url'
      elem = $compile('<confusion-matrix matrix=matrix url=url></confusion-matrix>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      expect(elem.html()).toContain 'some/url'
      expect(elem.html()).toContain 'head1'
      expect(elem.html()).toContain 'head2'
      expect(elem.html()).toContain '999'
      expect(elem.html()).toContain '888'
      expect(elem.html()).toContain '777'
      expect(elem.html()).toContain '666'


  describe 'recursive', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'it should render with row', ->

      $scope.row = {full_name: 'zinger'}
      elem = $compile('<recursive>something</recursive>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      expect(elem.html()).toEqual ''

    it 'it should render without row', ->

      $scope.row = {row: {full_name: 'bringer'}}
      elem = $compile('<recursive>another thing</recursive>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      expect(elem.html()).toContain '<span class="ng-scope">another thing</span>'

  describe 'tree', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render', ->
      $scope.tree = {categories: {__cat1__:{}, __cat2__:{}},
      weights: {we1: {name: '__we1__', value: '__val1__'}, we2: {name: '__we2__', value: '__val2__'}}}
      $scope.click = jasmine.createSpy '$scope.click'
      elem = $compile('<span tree="tree" custom-click="click()"></span>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      for v in ['__cat1__', '__cat2__', '__we1__', '__we2__', '__val1__', '__val2__']
        expect(elem.html()).toContain v


  # TODO: nader20140911 need to figure a way to test html output on this massive
  # template
  describe 'entitiesTree', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render', ->
      $scope.handler =
        xml_data_sources: [
          type: 'ds'
          name: 'ds1'
          id: 111
        ,
          type: 'ds'
          name: 'ds2'
          id: 222
        ,
          type: 'another_type'
          name: 'ds3'
          id: 333
        ]
      elem = $compile('<entities-tree handler="handler"></entities-tree>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      treeScope = $('>ul', elem).scope()
      expect(treeScope.getDatasources('ds')).toEqual [{text: 'ds1', value: 111}, {text: 'ds2', value: 222}]
      expect(treeScope.getDatasources('another_type')).toEqual [{text: 'ds3', value: 333}]


  describe 'entitiesRecursive', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render', ->
      elem = $compile('<entities-recursive>zinger</entities-recursive>')($scope)
      $(document.body).append(elem)
      $scope.$digest()
      expect(elem.html()).toEqual '<span class="ng-scope">zinger</span>'


  describe 'paramsEditor', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render', ->
      $scope.params = {__key1__: {}, __key2__: {}}
      elem = $compile('<params-editor params="params"></params-editor>')($scope)
      $(document.body).append(elem)
      $scope.$digest()
      expect(elem.html()).toContain '__key1__'
      expect(elem.html()).toContain '__key2__'


  describe 'paramsRecursive', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render with object', ->
      $scope.val = {}
      elem = $compile('<params-recursive>zinger</params-recursive>')($scope)
      $(document.body).append(elem)
      $scope.$digest()
      expect(elem.html()).toEqual '<span class="ng-scope">zinger</span>'

    it 'should render without object', ->
      $scope.val = 'string'
      elem = $compile('<params-recursive>zinger</params-recursive>')($scope)
      $(document.body).append(elem)
      $scope.$digest()
      expect(elem.html()).toEqual ''


  describe "loadindicator", ->

    it "should create progress", ->
      element = $compile("""
<loadindicator title="Adding model..." cml-progress="savingProgress"></loadindicator>
""")($scope)

      $scope.savingProgress = '0%'
      $scope.$digest()
      expect(element.html()).toContain('<div class="progress progress-striped active">')
      expect(element.html()).toContain('class="bar"')
      expect(element.html()).toContain('width: 0%;')

      $scope.savingProgress = '10%'
      $scope.$digest()
      expect(element.html()).toContain('class="bar"')
      expect(element.html()).toContain('width: 10%;')

    it "should create spinner", ->
      element = $compile("""
<loadindicator title="Adding model..."></loadindicator>
""")($scope)

      $scope.$digest()
      expect(element[0].outerHTML).toContain('loading-indicator-spin')
      expect(element.html()).toContain('<img src="/img/ajax-loader.gif">')


  describe 'alertMessage', ->
    elem = null
    afterEach ->
      elem.remove()

    it 'should render with unsafe', ->
      $scope.msg = '<first-message>'
      $scope.htmlclass = 'first-class'
      elem = $compile('<alert-message htmlclass="{{ htmlclass }}"  msg="{{ msg }}" unsafe></alert-message>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      expect(elem.html()).toContain '&lt;first-message&gt;'
      expect(elem.hasClass('first-class')).toBe true

      # change message
      $scope.msg = '<second-message>'
      $scope.$digest()

      expect(elem.html()).not.toContain '&lt;first-message&gt;'
      expect(elem.html()).toContain '&lt;second-message&gt;'

      # change class
      $scope.htmlclass = 'second-class'
      $scope.$digest()

      expect(elem.hasClass('first-class')).toBe false
      expect(elem.hasClass('second-class')).toBe true

      # change class
      $scope.htmlclass = 'third-class'
      $scope.$digest()
      expect(elem.hasClass('first-class')).toBe false
      expect(elem.hasClass('second-class')).toBe false
      expect(elem.hasClass('third-class')).toBe true

    it 'should render with not unsafe', ->
      $scope.msg = '<first-message>'
      elem = $compile('<alert-message  msg="{{ msg }}"></alert-message>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      expect(elem.html()).toContain '<first-message>'

      # change message
      $scope.msg = '<second-message>'
      $scope.$digest()
      expect(elem.html()).not.toContain '<first-message>'
      expect(elem.html()).toContain '<second-message>'

  describe 'files manipulation', ->

    elem = null
    afterEach ->
      if elem
        elem.remove()

    getFileList = ->
      getABlob = ->
        if typeof(Blob) is typeof(Function)
          return new Blob(['same way...'], {type: 'text/plain'})
        else
          BlobBuilder = window.BlobBuilder or window.WebKitBlobBuilder or window.MozBlobBuilder or window.MSBlobBuilder
          builder = new BlobBuilder()
          builder.append 'same way...'
          return builder.getBlob()

      file = getABlob()
      fileList =
        0: file,
        length: 1,
        item: (index) -> file
      return fileList

    prepareContext = (html) ->
      elem = $compile(html)($scope)
      $(document.body).append(elem)
      $scope.$digest()

    describe 'jsonFile', ->
      it 'should render and handels file uploads with errors', inject ($timeout)->
        $scope.some_file = ''
        prepareContext '<form name="myForm"><input json-file type="file" name="some_file" ng-model="some_file"></form>'

        inputElem = $('>input', elem)
        inputElem.triggerHandler
          type: 'change'
          target:
            files: getFileList()

        #console.log '1'
        $scope.$digest()
        #console.log '4'
        # TODO: nader20140911, somehow the reade.onload is triggerd after the test
        # finishes and thus I cannot really test the validity of the input
        # enabling the console.log will create 1, 4, 2, 3 !


    describe 'notRequiredFile', ->

      it 'should compile', ->
        $scope.some_file = ''
        prepareContext '<form name="myForm"><input not-required-file type="file" name="some_file" ng-model="some_file"/></form>'

        inputElem = $('>input', elem)
        inputElem.triggerHandler
          type: 'change'
          target:
            files: getFileList()

        $scope.$digest()


    describe 'requiredFile', ->

      it 'should compile', ->
        $scope.model = {file: {}}
        prepareContext('<form name="myForm"><input type="file" name="some_file" ng-model="model.file" required-file/></form>')

        inputElem = $('>input', elem)
        inputElem.triggerHandler
          type: 'change'
          target:
            files: getFileList()

        $scope.$digest()


  describe 'smartFloat', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should', ->
      $scope.model = {tofloat: ''}
      elem = $compile('<form name="myform"><input name="tofloat" ng-model="model.tofloat" type="text" smart-float></form>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      $('>input', elem).val('asdfasd').change()
      $scope.$digest()
      expect($scope.myform.tofloat.$invalid).toBe true
      expect($scope.model.tofloat).toBeUndefined()

      $('>input', elem).val('-1,2').change()
      $scope.$digest()
      expect($scope.myform.tofloat.$invalid).toBe false
      expect($scope.model.tofloat).toBe -1.2


  describe 'ngModelOnblur', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should work', ->
      $scope.text = ''
      elem = $compile('<form name="myform"><input name="text" ng-model="text" type="text" ng-model-onblur></form>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      $('>input', elem).val 'something'
      $('>input', elem).trigger 'blur'
      expect($scope.text).toEqual 'something'



  describe "parametersEditor", ->

    elem = null
    innerScope = null
    afterEach ->
      if elem
        elem.remove()

    prepareContext = (html)->
      elem = $compile(html)($scope)
      $(document.body).append elem
      $scope.$digest()
      innerScope = $('>parameters-editor', elem).children().scope()

    it "should create parameters editor control with string parameter", ->

      $scope.paramsConfig = {"str_param": {"type": "str"}, strange: {type: null}}
      $scope.requiredParams = ["str_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # get type -- we are doing it here to be able to get the invalid type strange
      expect(innerScope.getType 'str_param').toEqual 'str'
      expect(innerScope.getType 'zinger').toEqual 'str'
      expect(innerScope.getType 'strange').toEqual 'str'

      # valid
      $scope.paramsConfig = {"str_param": {"type": "str"}}
      $scope.params = {"str_param": "value"}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>str_param</label>')

      # toggle collapse
      expect($scope.collapsed).toBeUndefined()
      innerScope.toggleCollapse()
      expect(innerScope.collapsed).toBe true
      expect(innerScope.chevron).toEqual 'icon-chevron-right'
      innerScope.toggleCollapse()
      expect(innerScope.collapsed).toBe false
      expect(innerScope.chevron).toEqual 'icon-chevron-down'


    it "should manipulate parameters", ->

      $scope.paramsConfig = {"str_param": {"type": "str"}, "dict_param": {"type": "dict"}}
      $scope.requiredParams = ["str_param"]
      $scope.optionalParams = []

      $rootScope.showAddKey = true
      $scope.params = {str_param: 'some string', dict_param: {}}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      expect(innerScope.isTopLevel()).toEqual true

      # moving str_param to dict_param will delete dict_param
      innerScope.moveKey innerScope.paramsEditorData, 'str_param', 'dict_param'
      expect(innerScope.paramsEditorData).toEqual {dict_param: 'some string'}

      # resetting
      $scope.params = {str_param: 'some string', dict_param: {}}
      $scope.$digest()

      # trying to delete required parameter fails
      innerScope.deleteKey innerScope.paramsEditorData, 'str_param'
      expect(innerScope.isRequired 'str_param').toBe true
      expect($window.alert).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string', dict_param: {}}

      # trying to delete non-required parameter and confirm false
      innerScope.deleteKey innerScope.paramsEditorData, 'dict_param'
      expect(innerScope.isRequired 'dict_param').toBe false
      expect($window.confirm).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string', dict_param: {}}

      # trying to delete non-required parameter and confirm true
      $window.confirm.andReturn true
      innerScope.deleteKey innerScope.paramsEditorData, 'dict_param'
      expect(innerScope.isRequired 'dict_param').toBe false
      expect($window.confirm).toHaveBeenCalled()
      expect(innerScope.paramsEditorData).toEqual {str_param: 'some string'}

      # adding item no key name
      innerScope.addItem innerScope.paramsEditorData
      expect($window.alert).toHaveBeenCalledWith 'Please fill in a name'

# TODO: nader20140912, continue adding new parameter logic
#      # adding item key name supplied, the click to trigger showAddKey = true
#      # there are two, we don't care which
#      expect($('a', elem).attr('title')).toEqual 'add new parameter'
#      $('a', elem).click()
#
#      expect($('.input-small .addItemKeyInput', elem).length).toEqual 1
#      expect($('.input-medium .addItemValueInput', elem)).length.toEqual 1
#      $('.input-small .addItemKeyInput', elem).val 'new key to test'
#      $('.input-medium .addItemValueInput', elem).val 'new key to test'
#      $('a', elem).scope().addItem innerScope.paramsEditorData
#      expect(innerScope.paramsEditorData).toEqual ''


    it "should create parameters editor control with object parameter", ->

      $scope.paramsConfig = {"map_param": {"type": "dict"}}
      $scope.requiredParams = ["map_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # valid
      $scope.params = {map_param: {one: 'one_val', two: 'two_val'}}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>map_param</label>')
      expect(elem.html()).toContain('<a title="add new parameter" ng-click="$parent.showAddKey = true"')

    it "should create parameters editor control with text parameter", ->
      $scope.params = {
        "text_param": '{"key": "val"}'
      }

      $scope.paramsConfig = {"text_param": {"type": "text"}}
      $scope.requiredParams = ["text_param"]
      $scope.optionalParams = []

      # invlaid
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # invalid json
      $scope.params = {text_param: 'invalid{"key":"value"}json'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      # valid
      $scope.params = {text_param: '{"key":"value"}'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe true
      expect($scope.myForm.$valid).toBe true

      expect(elem.html()).toContain('<div class="jsonContents ng-scope">')
      expect(elem.html()).toContain('<input ng-hide="isRequired(key)" ng-disabled="isRequired(key)"')
      expect(elem.html()).toContain('>text_param</label>')
      expect(elem.html()).toContain('<textarea name="text_param" ng-model="paramsEditorData[key]"')

    # TODO: this test takes too long
    it "should validate items", ->
      """
      Attention: As of Anguular 1.2.20 no need to call validate exciplictly
      as calling scope.digest() implicitly calls the validate
      """
      $scope.paramsConfig = {
        "str_param": {"type": "str"},
        "map_param": {"type": "dict"},
        "text_param": {"type": "text"}
      }
      $scope.requiredParams = ["str_param", "map_param", "text_param"]
      $scope.optionalParams = []

      # empty params
      $scope.params = {}
      prepareContext """
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
"""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams = ->
        $scope.params =
          map_param: {one: 'one_val', two: 'two_val'}
          str_param: "value"
          text_param: '{"key": "value"}'
        $scope.$digest()
        expect($scope.myForm.params.$valid).toBe true
        expect($scope.myForm.$valid).toBe true

      buildValidParams()
      $scope.params.map_param = {one: '', two: 'two_val'}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.map_param = {}
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['map_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.str_param = ""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['str_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.text_param = 'wrong{"key": "value"}json'
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      $scope.params.text_param = ""
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

      buildValidParams()
      delete $scope.params['text_param']
      $scope.$digest()
      expect($scope.myForm.params.$valid).toBe false
      expect($scope.myForm.$valid).toBe false

    # TODO: nader20140817: we need to work on adding new item after adopting
    # isloate scopes
    xit "should correctly add a new string item to object", ->

      $scope.paramsConfig = {"map_param": {"type": "dict"}}
      $scope.requiredParams = ["map_param"]
      $scope.optionalParams = []

      $scope.params = {map_param: {one: 'one_val', two: 'two_val'}}
      element = $compile("""
<form name="myForm">
<parameters-editor name="params" ng-model="params"
params-config="paramsConfig"
required-params="requiredParams"
optional-params="optionalParams"></parameters-editor>
</form>
""")($scope)
      $scope.$digest()

      addItem = angular.element(element.children().children()[0]).scope().addItem
      $scope.keyName = 'new_key'
      $scope.valueName = 'new_value'
      $scope.valueType = 'str'

      obj = {}
      addItem(obj)

      expect(obj.new_key).toEqual('new_value')


  describe 'scCurves', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should work', inject ($timeout)->
      $scope.curvesDict = {}
      elem = $compile('<sc-curves xlabel="False-positive rate" ylabel="True-positive rate" curves-dict="curvesDict" show-line="1" width="500"></sc-curves>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      $scope.curvesDict = {1:1}
      $scope.$digest()
      $timeout.flush()


  describe 'scChart', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should work', inject ($timeout) ->
      $scope.chartDict = {}
      elem = $compile('<sc-chart chart-dict="chartDict" width="150" height="150"></sc-chart>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      $scope.chartDict = {}
      $scope.$digest()
      $timeout.flush()


  describe 'ngDictInput', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should work', ->
      $scope.dictItem = {}
      elem = $compile('<form name="myform"><ng-dict-input name="dictItem" ng-model="dictItem"></ng-dict-input></form>')($scope)
      $(document.body).append(elem)
      $scope.$digest()
      textAreaElem = $('>ng-dict-input>textarea', elem)
      textAreaScope = textAreaElem.scope()
      expect(textAreaScope.displayValue).toBe '{}'

      textAreaScope.displayValue = angular.toJson {some: 'json'}
      textAreaScope.change() # I don't know what's automatically calls change()
      $scope.$digest()
      expect(textAreaScope.value).toEqual {some: 'json'}
      expect($scope.dictItem).toEqual {some: 'json'}

      # auto
      textAreaScope.displayValue = 'auto'
      textAreaScope.change() # I don't know what's automatically calls change()
      $scope.$digest()
      expect(textAreaScope.value).toEqual 'auto'
      expect($scope.dictItem).toEqual 'auto'


  describe 'ngName', ->
    elem = null
    afterEach ->
      if elem
        elem.remove()

    it 'should work', ->
      $scope.some_text = ''
      elem = $compile('<form name="myform"><input ng-name="zinger" type="text" ng-model="some_text"/></form>')($scope)
      $(document.body).append(elem)
      $scope.$digest()

      # TODO: nader20140911 this doesn't work I think because of new angularjs 1.2
      #expect($scope.myform.some_text.$name).toEqual 'zinger'
      #expect($('>input', elem).attr('name')).toEqual 'zinger'