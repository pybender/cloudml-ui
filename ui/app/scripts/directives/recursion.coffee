angular.module('app.directives')

.factory('RecursionHelper', ['$compile', ($compile) ->
    return {
        # /**
        #  * Manually compiles the element, fixing the recursion loop.
        #  * @param element
        #  * @param [link] A post-link function, or an object with function(s) registered via pre and post properties.
        #  * @returns An object containing the linking functions.
        #  */
        compile: (element, link) ->
            # Normalize the link parameter
            if(angular.isFunction(link))
                link = { post: link }

            # Break the recursion loop by removing the contents
            contents = element.contents().remove()
            compiledContents = undefined
            if (link && link.pre)
                pre = link.pre
            else 
                pre = null
            return {
                pre: pre,
                # /**
                #  * Compiles and re-adds the contents
                #  */
                post: (scope, element) ->
                    # Compile the contents
                    if (!compiledContents)
                        compiledContents = $compile(contents)

                    # Re-add the compiled contents to the element
                    compiledContents(scope, (clone) ->
                        element.append(clone)
                    )

                    # Call the post-linking function, if any
                    if (link && link.post)
                        link.post.apply(null, arguments)
            }
    }
])