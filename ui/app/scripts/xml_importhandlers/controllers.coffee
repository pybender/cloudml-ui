'use strict'

angular.module('app.xml_importhandlers.controllers', ['app.config', ])

.controller('XmlImportHandlerListCtrl', [
  '$scope'
  '$rootScope'
  'XmlImportHandler'

  ($scope, $rootScope, XmlImportHandler) ->
    $scope.MODEL = XmlImportHandler
    $scope.FIELDS = XmlImportHandler.MAIN_FIELDS
    $scope.ACTION = 'loading handler list'
])

.controller('BigListCtrl', [
  '$scope'
  '$location'

  ($scope, $location) ->
    $scope.currentTag = $location.search()['tag']
    $scope.kwargs = {
      tag: $scope.currentTag
      per_page: 5
      sort_by: 'updated_on'
      order: 'desc'
    }
    $scope.page = 1

    $scope.init = (updatedByMe, listUniqueName) ->
      $scope.listUniqueName = listUniqueName
      if updatedByMe
        $scope.$watch('user', (user, oldVal, scope) ->
          if user?
            $scope.filter_opts = {
              'updated_by_id': user.id
              'status': ''}
            $scope.$watch('filter_opts', (filter_opts, oldVal, scope) ->
              $scope.$emit 'BaseListCtrl:start:load', listUniqueName
            , true)
        , true)
      else
        $scope.filter_opts = {'status': ''}

    $scope.showMore = () ->
      $scope.page += 1
      extra = {'page': $scope.page}
      $scope.$emit 'BaseListCtrl:start:load', $scope.listUniqueName, true, extra
])

.controller('XmlImportHandlerDetailsCtrl', [
  '$scope'
  '$rootScope'
  '$routeParams'
  'XmlImportHandler'
  'Tag'

  ($scope, $rootScope, $routeParams, ImportHandler, Tag) ->
    if not $routeParams.id
      throw new Error "Can't initialize without import handler id"

    $scope.handler = new ImportHandler({id: $routeParams.id})
    $scope.params = {'tags': []}
    $scope.LOADED_SECTIONS = []
    $scope.PROCESS_STRATEGIES =
      _.sortBy ImportHandler.PROCESS_STRATEGIES, (s)-> s

    $scope.go = (section) ->
      fields = ''
      mainSection = section[0]
      if mainSection not in $scope.LOADED_SECTIONS
        # is not already loaded
        extraFields = ['xml_data_sources', 'xml_input_parameters', 'xml_scripts',
                       'entities', 'import_params', 'predict', 'can_edit', 'tags'].join(',')
        fields = "#{ImportHandler.MAIN_FIELDS},#{extraFields}"

      if section[1] == 'xml' then fields = 'xml'

      if fields isnt ''
        $scope.handler.$load
            show: fields
        .then (opts) ->
          if $scope.params['tags']?
            $scope.params['tags'] = []
            for t in $scope.handler.tags
              $scope.params['tags'].push {'id': t, 'text': t}
          $scope.LOADED_SECTIONS.push mainSection
          if mainSection is 'dataset'
            $scope.$broadcast('loadDataSet', true)
        , (opts) ->
          $scope.setError(opts, 'loading handler details')

    $scope.initSections($scope.go)

    $scope.select2params = {
      multiple: true
      query: (query) ->
        query.callback
          results: angular.copy($scope.tag_list)

      createSearchChoice: (term, data) ->
        cmp = () ->
          return this.text.localeCompare(term) == 0
        if $(data).filter(cmp).length == 0 then return {id: term, text: term}
    }

    Tag.$loadAll(
      show: 'text,id'
    ).then ((opts) ->
      $scope.tag_list = []
      for t in opts.objects
        if t.text?
          $scope.tag_list.push {'text': t.text, 'id': t.id}

    ), ((opts) ->
      $scope.setError(opts, 'loading tags')
    )

    $scope.$watch 'params.tags', (newVal, oldVal)->
      if angular.isString(newVal) and newVal isnt ''
        ids = newVal.split(',')
        $scope.params.tags = []
        for id in ids
          nId = _.parseInt(id)
          if nId
            $scope.params.tags.push (t for t in $scope.tag_list when t.id is nId)[0]
          else
            $scope.params.tags.push {id: id, text: id}

    $scope.updateTags = () ->
      $scope.handler.tags = []
      for t in $scope.params['tags']
        $scope.handler.tags.push t['text']

      $scope.handler.$save(only: ['tags'])
      .then (->), (opts)->
        $scope.setError opts, 'saving handler tags'
])


.controller('AddXmlImportHandlerCtl', [
  '$scope'
  'XmlImportHandler'

  ($scope, ImportHandler) ->
    $scope.types = [{name: 'Db'}, {name: 'Request'}]
    $scope.model = new ImportHandler()
])


.controller('PredictCtrl', [
  '$scope'

  ($scope) ->
    $scope.init = (handler) ->
      $scope.handler = handler
      $scope.kwargs = {'import_handler_id': handler.id}
      $scope.$watch('handler.predict', (predict, old, scope) ->
        if predict?
          #console.log handler, 12
          $scope.predict_models = predict.models
          $scope.predict = predict
          $scope.label = predict.label
          $scope.probability = predict.probability
      )
])
