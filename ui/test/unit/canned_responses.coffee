###
  This is responses to different url snatched from production for accurate testing
###

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
,
  key: 'multiclass model main fields'
  url_regex: new RegExp '^.+/cloudml/models/\\d+/\\?show=name%2Cstatus%2Ctest' +
    '_import_handler%2Ctrain_import_handler%2Ctrain_import_handler_type%2Ctes' +
    't_import_handler_type%2Ctest_handler_fields%2Clabels%2Cclassifier%2Cfeat' +
    'ures_set_id%2Csegments'
  data: """
  {"model": {"status": "Trained", "test_import_handler": {"name": "extract_3classes", "import_params": ["start", "end"], "created_on": "2014-07-02 01:35:44.623518", "updated_by_id": 1, "created_by_id": 1, "updated_on": "2014-07-02 01:35:44.637775", "data": {"target_schema": "bestmatch", "datasource": [{"db": {"vendor": "postgres", "conn": "host='localhost' dbname='cloudml' user='cloudml' password='cloudml'"}, "type": "sql", "name": "odw"}], "queries": [{"items": [{"target_features": [{"name": "application_id"}], "source": "application", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "opening_id"}], "source": "opening", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "hire_outcome"}], "source": "hire_outcome", "is_required": true, "process_as": "string"}, {"target_features": [{"jsonpath": "$.op_timezone", "name": "employer.op_timezone"}, {"jsonpath": "$.op_country_tz", "name": "employer.op_country_tz"}, {"jsonpath": "$.op_tot_jobs_filled", "name": "employer.op_tot_jobs_filled"}, {"jsonpath": "$.op_country", "name": "employer.country"}], "source": "employer_info", "is_required": true, "process_as": "json"}, {"target_features": [{"to_csv": true, "jsonpath": "$.skills.*.skl_name", "name": "contractor.skills"}, {"value_path": "$.*.ts_score", "jsonpath": "$.tsexams", "name": "tsexams", "key_path": "$.*.ts_name"}, {"jsonpath": "$.dev_adj_score_recent", "name": "contractor.dev_adj_score_recent"}, {"jsonpath": "$.dev_is_looking", "name": "contractor.dev_is_looking"}, {"jsonpath": "$.dev_recent_rank_percentile", "name": "contractor.dev_recent_rank_percentile"}, {"jsonpath": "$.dev_recent_fp_jobs", "name": "contractor.dev_recent_fp_jobs"}, {"jsonpath": "$.dev_recent_hours", "name": "contractor.dev_recent_hours"}, {"jsonpath": "$.dev_skill_test_passed_count", "name": "contractor.dev_skill_test_passed_count"}, {"jsonpath": "$.dev_total_hourly_jobs", "name": "contractor.dev_total_hourly_jobs"}, {"jsonpath": "$.dev_tot_feedback_recent", "name": "contractor.dev_tot_feedback_recent"}, {"jsonpath": "$.dev_rank_percentile", "name": "contractor.dev_rank_percentile"}, {"jsonpath": "$.dev_billed_assignments", "name": "contractor.dev_billed_assignments"}, {"jsonpath": "$.dev_is_looking_week", "name": "contractor.dev_is_looking_week"}, {"jsonpath": "$.dev_availability", "name": "contractor.dev_availability"}, {"jsonpath": "$.dev_total_revenue", "name": "contractor.dev_total_revenue"}, {"jsonpath": "$.dev_bill_rate", "name": "contractor.dev_bill_rate"}, {"jsonpath": "$.dev_test_passed_count", "name": "contractor.dev_test_passed_count"}, {"jsonpath": "$.dev_expose_full_name", "name": "contractor.dev_expose_full_name"}, {"jsonpath": "$.dev_total_hours_rounded", "name": "contractor.dev_total_hours_rounded"}, {"jsonpath": "$.dev_year_exp", "name": "contractor.dev_year_exp"}, {"jsonpath": "$.dev_portfolio_items_count", "name": "contractor.dev_portfolio_items_count"}, {"jsonpath": "$.dev_eng_skill", "name": "contractor.dev_eng_skill"}, {"jsonpath": "$.dev_tot_feedback", "name": "contractor.dev_tot_feedback"}, {"jsonpath": "$.dev_timezone", "name": "contractor.dev_timezone"}, {"jsonpath": "$.dev_last_worked", "name": "contractor.dev_last_worked"}, {"jsonpath": "$.dev_profile_title", "name": "contractor.dev_profile_title"}, {"jsonpath": "$.dev_active_interviews", "name": "contractor.dev_active_interviews"}, {"jsonpath": "$.dev_cur_assignments", "name": "contractor.dev_cur_assignments"}, {"jsonpath": "$.dev_pay_rate", "name": "contractor.dev_pay_rate"}, {"jsonpath": "$.dev_blurb", "name": "contractor.dev_blurb"}, {"jsonpath": "$.dev_country", "name": "contractor.dev_country"}], "source": "contractor_info", "is_required": true, "process_as": "json"}, {"target_features": [{"expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}, "name": "country_pair"}], "process_as": "composite"}], "name": "retrieve", "sql": "SELECT qi.*, 'class' || (trunc(random() * 3) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);"}]}, "id": 14}, "train_import_handler_type": "json", "test_handler_fields": ["application_id", "opening_id", "hire_outcome", "employer->op_timezone", "employer->op_country_tz", "employer->op_tot_jobs_filled", "employer->country", "contractor->skills", "tsexams", "contractor->dev_adj_score_recent", "contractor->dev_is_looking", "contractor->dev_recent_rank_percentile", "contractor->dev_recent_fp_jobs", "contractor->dev_recent_hours", "contractor->dev_skill_test_passed_count", "contractor->dev_total_hourly_jobs", "contractor->dev_tot_feedback_recent", "contractor->dev_rank_percentile", "contractor->dev_billed_assignments", "contractor->dev_is_looking_week", "contractor->dev_availability", "contractor->dev_total_revenue", "contractor->dev_bill_rate", "contractor->dev_test_passed_count", "contractor->dev_expose_full_name", "contractor->dev_total_hours_rounded", "contractor->dev_year_exp", "contractor->dev_portfolio_items_count", "contractor->dev_eng_skill", "contractor->dev_tot_feedback", "contractor->dev_timezone", "contractor->dev_last_worked", "contractor->dev_profile_title", "contractor->dev_active_interviews", "contractor->dev_cur_assignments", "contractor->dev_pay_rate", "contractor->dev_blurb", "contractor->dev_country", "country_pair"], "name": "multiclass_labels", "segments": [{"records": 96, "id": 10, "name": "default", "model_id": 5566}], "train_import_handler": {"name": "extract_3classes", "import_params": ["start", "end"], "created_on": "2014-07-02 01:35:44.623518", "updated_by_id": 1, "created_by_id": 1, "updated_on": "2014-07-02 01:35:44.637775", "data": {"target_schema": "bestmatch", "datasource": [{"db": {"vendor": "postgres", "conn": "host='localhost' dbname='cloudml' user='cloudml' password='cloudml'"}, "type": "sql", "name": "odw"}], "queries": [{"items": [{"target_features": [{"name": "application_id"}], "source": "application", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "opening_id"}], "source": "opening", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "hire_outcome"}], "source": "hire_outcome", "is_required": true, "process_as": "string"}, {"target_features": [{"jsonpath": "$.op_timezone", "name": "employer.op_timezone"}, {"jsonpath": "$.op_country_tz", "name": "employer.op_country_tz"}, {"jsonpath": "$.op_tot_jobs_filled", "name": "employer.op_tot_jobs_filled"}, {"jsonpath": "$.op_country", "name": "employer.country"}], "source": "employer_info", "is_required": true, "process_as": "json"}, {"target_features": [{"to_csv": true, "jsonpath": "$.skills.*.skl_name", "name": "contractor.skills"}, {"value_path": "$.*.ts_score", "jsonpath": "$.tsexams", "name": "tsexams", "key_path": "$.*.ts_name"}, {"jsonpath": "$.dev_adj_score_recent", "name": "contractor.dev_adj_score_recent"}, {"jsonpath": "$.dev_is_looking", "name": "contractor.dev_is_looking"}, {"jsonpath": "$.dev_recent_rank_percentile", "name": "contractor.dev_recent_rank_percentile"}, {"jsonpath": "$.dev_recent_fp_jobs", "name": "contractor.dev_recent_fp_jobs"}, {"jsonpath": "$.dev_recent_hours", "name": "contractor.dev_recent_hours"}, {"jsonpath": "$.dev_skill_test_passed_count", "name": "contractor.dev_skill_test_passed_count"}, {"jsonpath": "$.dev_total_hourly_jobs", "name": "contractor.dev_total_hourly_jobs"}, {"jsonpath": "$.dev_tot_feedback_recent", "name": "contractor.dev_tot_feedback_recent"}, {"jsonpath": "$.dev_rank_percentile", "name": "contractor.dev_rank_percentile"}, {"jsonpath": "$.dev_billed_assignments", "name": "contractor.dev_billed_assignments"}, {"jsonpath": "$.dev_is_looking_week", "name": "contractor.dev_is_looking_week"}, {"jsonpath": "$.dev_availability", "name": "contractor.dev_availability"}, {"jsonpath": "$.dev_total_revenue", "name": "contractor.dev_total_revenue"}, {"jsonpath": "$.dev_bill_rate", "name": "contractor.dev_bill_rate"}, {"jsonpath": "$.dev_test_passed_count", "name": "contractor.dev_test_passed_count"}, {"jsonpath": "$.dev_expose_full_name", "name": "contractor.dev_expose_full_name"}, {"jsonpath": "$.dev_total_hours_rounded", "name": "contractor.dev_total_hours_rounded"}, {"jsonpath": "$.dev_year_exp", "name": "contractor.dev_year_exp"}, {"jsonpath": "$.dev_portfolio_items_count", "name": "contractor.dev_portfolio_items_count"}, {"jsonpath": "$.dev_eng_skill", "name": "contractor.dev_eng_skill"}, {"jsonpath": "$.dev_tot_feedback", "name": "contractor.dev_tot_feedback"}, {"jsonpath": "$.dev_timezone", "name": "contractor.dev_timezone"}, {"jsonpath": "$.dev_last_worked", "name": "contractor.dev_last_worked"}, {"jsonpath": "$.dev_profile_title", "name": "contractor.dev_profile_title"}, {"jsonpath": "$.dev_active_interviews", "name": "contractor.dev_active_interviews"}, {"jsonpath": "$.dev_cur_assignments", "name": "contractor.dev_cur_assignments"}, {"jsonpath": "$.dev_pay_rate", "name": "contractor.dev_pay_rate"}, {"jsonpath": "$.dev_blurb", "name": "contractor.dev_blurb"}, {"jsonpath": "$.dev_country", "name": "contractor.dev_country"}], "source": "contractor_info", "is_required": true, "process_as": "json"}, {"target_features": [{"expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}, "name": "country_pair"}], "process_as": "composite"}], "name": "retrieve", "sql": "SELECT qi.*, 'class' || (trunc(random() * 3) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);"}]}, "id": 14}, "classifier": {"type": "logistic regression", "params": {"penalty": "l2"}}, "labels": ["1", "2", "3"], "test_import_handler_type": "json", "id": 5566, "features_set_id": 5566}}
  """
  type: 'json'
  status: 'OK'
  statusCode: 200
]