
class JsonSerializableMixin(object):

    def __json__(self):
        """
        Converts all the properties of the object into a dict for use in json.
        You can define the following in your class

        _json_eager_load :
            list of which child classes need to be eagerly loaded. This applies
            to one-to-many relationships defined in SQLAlchemy classes.

        _base_blacklist :
            top level blacklist list of which properties not to include in JSON

        _json_blacklist :
            blacklist list of which properties not to include in JSON

        :return: dictionary ready to be jsonified
        :rtype: <dict>
        """
        props = {}

        # grab the json_eager_load set, if it exists
        # use set for easy 'in' lookups
        json_eager_load = set(getattr(self, '_json_eager_load', []))
        # now load the property if it exists
        # (does this issue too many SQL statements?)
        for prop in json_eager_load:
            getattr(self, prop, None)

        # we make a copy because the dict will change if the database
        # is updated / flushed
        options = self.__dict__.copy()

        # setup the blacklist
        # use set for easy 'in' lookups
        blacklist = set(getattr(self, '_base_blacklist', []))
        # extend the base blacklist with the json blacklist
        blacklist.update(getattr(self, '_json_blacklist', []))

        for key in options:
            # skip blacklisted, private and SQLAlchemy properties
            if key in blacklist or key.startswith(('__', '_sa_')):
                continue

            # format and date/datetime/time properties to isoformat
            obj = getattr(self, key)
            if isinstance(obj, (datetime, date, time)):
                props[key] = obj.isoformat()
            else:
                # get the class property value
                attr = getattr(self, key)
                # let see if we need to eagerly load it
                if key in json_eager_load:
                    # this is for SQLAlchemy foreign key fields that
                    # indicate with one-to-many relationships
                    if not hasattr(attr, 'pk') and attr:
                        # jsonify all child objects
                        attr = [x.__json__() for x in attr]
                else:
                    # convert all non integer strings to string or if
                    # string conversion is not possible, convert it to
                    # Unicode
                    if attr and not isinstance(attr, (int, float)):
                        try:
                            attr = str(attr)
                        except UnicodeEncodeError:
                            attr = unicode(attr)  # .encode('utf-8')

                props[key] = attr

        return props
