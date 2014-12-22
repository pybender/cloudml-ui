angular.module('app.directives')

.directive('themeSelector', [ '$timeout', '$cookieStore',
  ($timeout, $cookieStore)->
    themes = ['default', 'simplex', 'united', 'flatly', 'spacelab', 'readable',
              'cosmo', 'cerulean', 'slate', 'amelia']

    selector = ''
    for theme in themes
      selector += """
            <li ng-class="{true: 'active', false: ''}[selectedTheme == '#{theme}']">
              <a ng-click="changeTheme('#{theme}')">#{theme}</a></li>
      """

    return {
      restrict: 'E'
      template: """
        <li class="dropdown">
          <a class="dropdown-toggle" data-toggle="dropdown">theme <b class="caret"></b></a>
          <ul class="dropdown-menu">#{selector}</ul>
        </li>
      """
      replace: true
      link: (scope, element, attributes, ngModel) ->

        scope.changeTheme = (newTheme)->
          if newTheme not in themes
            console.warn 'unkown theme', newTheme
            return false

          $cookieStore.put 'theme', newTheme
          scope.selectedTheme = newTheme
          $("link[id='theTheme']", document).attr('remove', 'true')
          $('head', document).prepend("""
            <link id="theTheme" rel="stylesheet" href="/css/app_#{newTheme}.css">
          """)
          $timeout ->
            $("link[id='theTheme'][remove='true']", document).remove()
          , 100
          return false

        # TODO: nader20141222 - we should be reading configured theme from a cookie
        scope.changeTheme($cookieStore.get('theme') or 'default')
    }
  ])
