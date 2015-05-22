# Authors: Nikolay Melnik <nmelnik@upwork.com>

from flask.ext import restful

__all__ = ["Api"]


class Api(restful.Api):
    """
    REST API class
    """
    def add_resource(self, resource, *urls, **kwargs):
        """Adds a resource to the api.

        :param resource: the class name of your resource
        :type resource: Resource
        :param urls: one or more url routes to match for the resource, standard
                     flask routing rules apply.  Any url variables will be
                     passed to the resource method as args.
        :type urls: str

        :param endpoint: endpoint name (defaults to Resource.__name__.lower()
                         can be used to reference this route in Url fields
                         see: Fields
        :type endpoint: str


        Examples:
            api.add_resource(HelloWorld, '/', '/hello')
        """
        add_standard_urls = kwargs.get('add_standard_urls', True)
        endpoint = kwargs.get('endpoint') or resource.__name__.lower()

        if endpoint in self.app.view_functions.keys():
            previous_view_class = \
                self.app.view_functions[endpoint].func_dict['view_class']
            if previous_view_class != resource:
                raise ValueError(
                    'This endpoint (%s) is already set to the class %s.' %
                    (endpoint, previous_view_class.__name__))

        resource.mediatypes = self.mediatypes_method()  # Hacky
        resource_func = self.output(resource.as_view(endpoint))

        for decorator in self.decorators:
            resource_func = decorator(resource_func)

        for part in urls:
            base_url = self.prefix + part
            self.app.add_url_rule(base_url, view_func=resource_func)

            if add_standard_urls:
                def add_url(end):
                    self.app.add_url_rule(
                        "{0!s}{1!s}".format(base_url, end),
                        view_func=resource_func)

                add_url('<regex("[\w\.-]*"):id>/')
                add_url('action/<regex("[\w\.]*"):action>/')
                add_url(
                    '<regex("[\w\.-]*"):id>/action/<regex("[\w\.]*"):action>/')

    def handle_error(self, e):
        """ Note this method returns a Flask Response object """
        from api.base.resources.utils import _add_cors_headers

        resp = super(Api, self).handle_error(e)
        _add_cors_headers(resp.headers)
        return resp
