###
  This is responses to different url snatched from production for accurate testing
###
# TODO: we need too configure brunch to exclude this file from the code generation

map_url_to_response = (url, key)->
  """
  @url: the url to match the regex against
  @key: the key of canned response as defined in the canned responses list
  @returns: null if url/key pair doesn't match or a list to be supplied
  to angular requestHandler as defined in
  https://docs.angularjs.org/api/ngMock/service/$httpBackend
"""
  resp = null
  for v in CANNED_RESPONSES
    if key is v.key and v.url_regex.test url
      resp = v
      break
  if not resp
    null
  return [
    resp.statusCode
    resp.data
    null
    resp.status
  ]

CANNED_RESPONSES = [
  key: 'multiclass classification model dict format (after 20140710)'
  url_regex: new RegExp '^.+/cloudml/models/\\d+/tests/\\d+/\\?show=' +
                        'accuracy%2Cmetrics%2Cexamples_placement%2Cname' +
                        '%2Cstatus%2Ccreated_on%2Ccreated_by?'
  data: """
{"test": {"status": "Completed", "name": "Test1", "examples_placement": null,
"created_by": {"portrait_32_img": "url1", "uid": "nsoliman", "auth_token":
"authtoken2", "odesk_url": "url2", "id": 1, "created_on": "2014-06-04",
"updated_on": "2014-07-01", "email": "nsoliman@odesk.com",
"name": "Nader Soliman"}, "metrics": {"roc_auc":
{"1": 1.0, "3": 1.0, "2": 0.99658203125}, "confusion_matrix": [["1", [29, 0, 0]],
["2", [1, 31, 0]], ["3", [0, 0, 35]]], "roc_curve": {"1": [[0.0, 0.0, 0.0, 0.0],
[0.034, 0.06, 0.10, 0.13]], "3": [[0.0, 0.0, 0.0, 0.0], [0.028, 0.05, 0.08, 0.11]],
"2": [[0.0, 0.0, 0.0, 0.0], [0.031, 0.06, 0.09, 0.125]]}, "accuracy": 0.98},
"created_on": "2014-07-11", "id": 38, "accuracy": 0.98}}
"""
  type: 'json'
  status: 'OK'
  statusCode: 200
,
  key: 'binary classification model dict format (after 20140710)'
  url_regex: new RegExp '^.+/cloudml/models/\\d+/tests/\\d+/\\?show=' +
    'accuracy%2Cmetrics%2Cexamples_placement%2Cname' +
    '%2Cstatus%2Ccreated_on%2Ccreated_by?'
  data: """
{"test": {"status": "Completed", "name": "Test2", "examples_placement": null,
"created_by": {"portrait_32_img": "url1", "uid": "nsoliman", "auth_token":
"authtoken1", "odesk_url": "url2", "id": 1, "created_on": "2014-06-04",
"updated_on": "2014-07-01", "email": "nsoliman@odesk.com",
"name": "Nader Soliman"}, "metrics": {"avarage_precision": 0.0, "roc_curve":
{"1": [[0.0, 0.0, 0.0, 0.0], [0.02, 0.04, 0.06, 0.08]]}, "roc_auc": {"1": 1.0},
"confusion_matrix": [["0", [45, 1]], ["1", [0, 50]]], "precision_recall_curve":
[[1.0, 1.0, 1.0, 1.0], [1.0, 0.98, 0.96, 0.94]], "accuracy": 0.98},
"created_on": "2014-07-11", "id": 37, "accuracy": 0.98}}
"""
  type: 'json'
  status: 'OK'
  statusCode: 200
,
  key: 'binary classification arrays format (before 20140710)'
  url_regex: new RegExp '^.+/cloudml/models/\\d+/tests/\\d+/\\?show=' +
    'accuracy%2Cmetrics%2Cexamples_placement%2Cname' +
    '%2Cstatus%2Ccreated_on%2Ccreated_by?'
  data: """
{"test": {"status": "Completed", "name": "Test1", "examples_placement": null,
"created_by": {"portrait_32_img": "someurl1", "uid": "nsoliman", "auth_token":
"authtoken1", "odesk_url": "someurl2", "id": 1, "created_on": "2014-06-04",
"updated_on": "2014-07-01 13:55:57.459741", "email": "nsoliman@odesk.com",
"name": "Nader Soliman"}, "metrics": {"avarage_precision": 0.0, "roc_curve":
[[0.0, 0.009, 0.019, 0.029], [0.0, 0.04, 0.05, 0.071]], "roc_auc": 0.775,
"confusion_matrix": [["False", [23212, 2565]], ["True", [247, 102]]],
"precision_recall_curve": [[0.015, 0.015, 0.015, 0.015], [1.0, 0.99, 0.99, 0.99]],
"accuracy": 0.892}, "created_on": "2014-07-02 18:11:27.275686", "id": 5,
"accuracy": 0.98}}
"""
  type: 'json'
  status: 'OK'
  statusCode: 200
]