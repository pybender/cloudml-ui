
toListOfDictWithFields = (objects, fields) ->
  """
  Converts list of the objects to list of dictionaries with
  specified fields.

    objects: list of objects or dictionaries
    fields: fields, which are should be present in result list
"""
  if fields.indexOf('id') == -1 
    fields.push 'id'  # API always returns id of the object
  res = []
  for obj in objects
    item = {}
    for field in fields
      item[field] = obj[field]
    res.push item
  return res

buildListResponse = (objects, fields) ->
  """
  Converts list of the objects to the REST API GET list response.

    objects: list of objects
    fields: fields, which are should be present in response.
"""
  obj = objects[0]
  resp = {}
  resp[obj.API_FIELDNAME + 's'] = toListOfDictWithFields(objects, fields)
  return angular.toJson(resp)
