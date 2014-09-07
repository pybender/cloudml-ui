###
  This is responses to different url snatched from production for accurate testing
###
if jasmine.version? #the case for version 2.0.0
  console.log "jasmine-version:#{jasmine.version}"
else # the case for version 1.3
  console.log "jasmine-version:#{jasmine.getEnv().versionString()}"

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
                        'accuracy,metrics,examples_placement,name' +
                        ',status,created_on,created_by?'
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
    'accuracy,metrics,examples_placement,name' +
    ',status,created_on,created_by?'
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
    'accuracy,metrics,examples_placement,name' +
    ',status,created_on,created_by?'
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
  url_regex: new RegExp '^.+/cloudml/models/\\d+/\\?show=name,status,test' +
    '_import_handler,train_import_handler,train_import_handler_type,tes' +
    't_import_handler_type,test_handler_fields,labels,classifier,feat' +
    'ures_set_id,segments'
  data: """
  {"model": {"status": "Trained", "test_import_handler": {"name": "extract_3classes", "import_params": ["start", "end"], "created_on": "2014-07-02 01:35:44.623518", "updated_by_id": 1, "created_by_id": 1, "updated_on": "2014-07-02 01:35:44.637775", "data": {"target_schema": "bestmatch", "datasource": [{"db": {"vendor": "postgres", "conn": "host='localhost' dbname='cloudml' user='cloudml' password='cloudml'"}, "type": "sql", "name": "odw"}], "queries": [{"items": [{"target_features": [{"name": "application_id"}], "source": "application", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "opening_id"}], "source": "opening", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "hire_outcome"}], "source": "hire_outcome", "is_required": true, "process_as": "string"}, {"target_features": [{"jsonpath": "$.op_timezone", "name": "employer.op_timezone"}, {"jsonpath": "$.op_country_tz", "name": "employer.op_country_tz"}, {"jsonpath": "$.op_tot_jobs_filled", "name": "employer.op_tot_jobs_filled"}, {"jsonpath": "$.op_country", "name": "employer.country"}], "source": "employer_info", "is_required": true, "process_as": "json"}, {"target_features": [{"to_csv": true, "jsonpath": "$.skills.*.skl_name", "name": "contractor.skills"}, {"value_path": "$.*.ts_score", "jsonpath": "$.tsexams", "name": "tsexams", "key_path": "$.*.ts_name"}, {"jsonpath": "$.dev_adj_score_recent", "name": "contractor.dev_adj_score_recent"}, {"jsonpath": "$.dev_is_looking", "name": "contractor.dev_is_looking"}, {"jsonpath": "$.dev_recent_rank_percentile", "name": "contractor.dev_recent_rank_percentile"}, {"jsonpath": "$.dev_recent_fp_jobs", "name": "contractor.dev_recent_fp_jobs"}, {"jsonpath": "$.dev_recent_hours", "name": "contractor.dev_recent_hours"}, {"jsonpath": "$.dev_skill_test_passed_count", "name": "contractor.dev_skill_test_passed_count"}, {"jsonpath": "$.dev_total_hourly_jobs", "name": "contractor.dev_total_hourly_jobs"}, {"jsonpath": "$.dev_tot_feedback_recent", "name": "contractor.dev_tot_feedback_recent"}, {"jsonpath": "$.dev_rank_percentile", "name": "contractor.dev_rank_percentile"}, {"jsonpath": "$.dev_billed_assignments", "name": "contractor.dev_billed_assignments"}, {"jsonpath": "$.dev_is_looking_week", "name": "contractor.dev_is_looking_week"}, {"jsonpath": "$.dev_availability", "name": "contractor.dev_availability"}, {"jsonpath": "$.dev_total_revenue", "name": "contractor.dev_total_revenue"}, {"jsonpath": "$.dev_bill_rate", "name": "contractor.dev_bill_rate"}, {"jsonpath": "$.dev_test_passed_count", "name": "contractor.dev_test_passed_count"}, {"jsonpath": "$.dev_expose_full_name", "name": "contractor.dev_expose_full_name"}, {"jsonpath": "$.dev_total_hours_rounded", "name": "contractor.dev_total_hours_rounded"}, {"jsonpath": "$.dev_year_exp", "name": "contractor.dev_year_exp"}, {"jsonpath": "$.dev_portfolio_items_count", "name": "contractor.dev_portfolio_items_count"}, {"jsonpath": "$.dev_eng_skill", "name": "contractor.dev_eng_skill"}, {"jsonpath": "$.dev_tot_feedback", "name": "contractor.dev_tot_feedback"}, {"jsonpath": "$.dev_timezone", "name": "contractor.dev_timezone"}, {"jsonpath": "$.dev_last_worked", "name": "contractor.dev_last_worked"}, {"jsonpath": "$.dev_profile_title", "name": "contractor.dev_profile_title"}, {"jsonpath": "$.dev_active_interviews", "name": "contractor.dev_active_interviews"}, {"jsonpath": "$.dev_cur_assignments", "name": "contractor.dev_cur_assignments"}, {"jsonpath": "$.dev_pay_rate", "name": "contractor.dev_pay_rate"}, {"jsonpath": "$.dev_blurb", "name": "contractor.dev_blurb"}, {"jsonpath": "$.dev_country", "name": "contractor.dev_country"}], "source": "contractor_info", "is_required": true, "process_as": "json"}, {"target_features": [{"expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}, "name": "country_pair"}], "process_as": "composite"}], "name": "retrieve", "sql": "SELECT qi.*, 'class' || (trunc(random() * 3) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);"}]}, "id": 14}, "train_import_handler_type": "json", "test_handler_fields": ["application_id", "opening_id", "hire_outcome", "employer->op_timezone", "employer->op_country_tz", "employer->op_tot_jobs_filled", "employer->country", "contractor->skills", "tsexams", "contractor->dev_adj_score_recent", "contractor->dev_is_looking", "contractor->dev_recent_rank_percentile", "contractor->dev_recent_fp_jobs", "contractor->dev_recent_hours", "contractor->dev_skill_test_passed_count", "contractor->dev_total_hourly_jobs", "contractor->dev_tot_feedback_recent", "contractor->dev_rank_percentile", "contractor->dev_billed_assignments", "contractor->dev_is_looking_week", "contractor->dev_availability", "contractor->dev_total_revenue", "contractor->dev_bill_rate", "contractor->dev_test_passed_count", "contractor->dev_expose_full_name", "contractor->dev_total_hours_rounded", "contractor->dev_year_exp", "contractor->dev_portfolio_items_count", "contractor->dev_eng_skill", "contractor->dev_tot_feedback", "contractor->dev_timezone", "contractor->dev_last_worked", "contractor->dev_profile_title", "contractor->dev_active_interviews", "contractor->dev_cur_assignments", "contractor->dev_pay_rate", "contractor->dev_blurb", "contractor->dev_country", "country_pair"], "name": "multiclass_labels", "segments": [{"records": 96, "id": 10, "name": "default", "model_id": 5566}], "train_import_handler": {"name": "extract_3classes", "import_params": ["start", "end"], "created_on": "2014-07-02 01:35:44.623518", "updated_by_id": 1, "created_by_id": 1, "updated_on": "2014-07-02 01:35:44.637775", "data": {"target_schema": "bestmatch", "datasource": [{"db": {"vendor": "postgres", "conn": "host='localhost' dbname='cloudml' user='cloudml' password='cloudml'"}, "type": "sql", "name": "odw"}], "queries": [{"items": [{"target_features": [{"name": "application_id"}], "source": "application", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "opening_id"}], "source": "opening", "is_required": true, "process_as": "string"}, {"target_features": [{"name": "hire_outcome"}], "source": "hire_outcome", "is_required": true, "process_as": "string"}, {"target_features": [{"jsonpath": "$.op_timezone", "name": "employer.op_timezone"}, {"jsonpath": "$.op_country_tz", "name": "employer.op_country_tz"}, {"jsonpath": "$.op_tot_jobs_filled", "name": "employer.op_tot_jobs_filled"}, {"jsonpath": "$.op_country", "name": "employer.country"}], "source": "employer_info", "is_required": true, "process_as": "json"}, {"target_features": [{"to_csv": true, "jsonpath": "$.skills.*.skl_name", "name": "contractor.skills"}, {"value_path": "$.*.ts_score", "jsonpath": "$.tsexams", "name": "tsexams", "key_path": "$.*.ts_name"}, {"jsonpath": "$.dev_adj_score_recent", "name": "contractor.dev_adj_score_recent"}, {"jsonpath": "$.dev_is_looking", "name": "contractor.dev_is_looking"}, {"jsonpath": "$.dev_recent_rank_percentile", "name": "contractor.dev_recent_rank_percentile"}, {"jsonpath": "$.dev_recent_fp_jobs", "name": "contractor.dev_recent_fp_jobs"}, {"jsonpath": "$.dev_recent_hours", "name": "contractor.dev_recent_hours"}, {"jsonpath": "$.dev_skill_test_passed_count", "name": "contractor.dev_skill_test_passed_count"}, {"jsonpath": "$.dev_total_hourly_jobs", "name": "contractor.dev_total_hourly_jobs"}, {"jsonpath": "$.dev_tot_feedback_recent", "name": "contractor.dev_tot_feedback_recent"}, {"jsonpath": "$.dev_rank_percentile", "name": "contractor.dev_rank_percentile"}, {"jsonpath": "$.dev_billed_assignments", "name": "contractor.dev_billed_assignments"}, {"jsonpath": "$.dev_is_looking_week", "name": "contractor.dev_is_looking_week"}, {"jsonpath": "$.dev_availability", "name": "contractor.dev_availability"}, {"jsonpath": "$.dev_total_revenue", "name": "contractor.dev_total_revenue"}, {"jsonpath": "$.dev_bill_rate", "name": "contractor.dev_bill_rate"}, {"jsonpath": "$.dev_test_passed_count", "name": "contractor.dev_test_passed_count"}, {"jsonpath": "$.dev_expose_full_name", "name": "contractor.dev_expose_full_name"}, {"jsonpath": "$.dev_total_hours_rounded", "name": "contractor.dev_total_hours_rounded"}, {"jsonpath": "$.dev_year_exp", "name": "contractor.dev_year_exp"}, {"jsonpath": "$.dev_portfolio_items_count", "name": "contractor.dev_portfolio_items_count"}, {"jsonpath": "$.dev_eng_skill", "name": "contractor.dev_eng_skill"}, {"jsonpath": "$.dev_tot_feedback", "name": "contractor.dev_tot_feedback"}, {"jsonpath": "$.dev_timezone", "name": "contractor.dev_timezone"}, {"jsonpath": "$.dev_last_worked", "name": "contractor.dev_last_worked"}, {"jsonpath": "$.dev_profile_title", "name": "contractor.dev_profile_title"}, {"jsonpath": "$.dev_active_interviews", "name": "contractor.dev_active_interviews"}, {"jsonpath": "$.dev_cur_assignments", "name": "contractor.dev_cur_assignments"}, {"jsonpath": "$.dev_pay_rate", "name": "contractor.dev_pay_rate"}, {"jsonpath": "$.dev_blurb", "name": "contractor.dev_blurb"}, {"jsonpath": "$.dev_country", "name": "contractor.dev_country"}], "source": "contractor_info", "is_required": true, "process_as": "json"}, {"target_features": [{"expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}, "name": "country_pair"}], "process_as": "composite"}], "name": "retrieve", "sql": "SELECT qi.*, 'class' || (trunc(random() * 3) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);"}]}, "id": 14}, "classifier": {"type": "logistic regression", "params": {"penalty": "l2"}}, "labels": ["1", "2", "3"], "test_import_handler_type": "json", "id": 5566, "features_set_id": 5566}}
  """
  type: 'json'
  status: 'OK'
  statusCode: 200
,
  key: 'load parameters configuration'
  url_regex: new RegExp '^.+/cloudml/features/params/'
  data: """
{"configuration": {"params": {"pattern": {"help_text": "Please enter a pattern", "type": "str"}, "chain": {"help_text": "Please enter valid json", "type": "text"}, "mappings": {"help_text": "Please add parameters to dictionary", "type": "dict"}, "split_pattern": {"help_text": "Please enter a pattern", "type": "str"}, "min_df": {"help_text": "Please enter a int value", "type": "int"}}, "defaults": {"date": 946684800}, "types": {"regex": {"optional_params": [], "type": "", "default_params": [], "required_params": ["pattern"]}, "map": {"optional_params": [], "type": "", "default_params": [], "required_params": ["mappings"]}, "categorical": {"optional_params": ["split_pattern", "min_df"], "type": "", "default_params": [], "required_params": []}, "composite": {"optional_params": [], "type": "", "default_params": [], "required_params": ["chain"]}, "text": {"optional_params": [], "type": "<type 'str'>", "default_params": [], "required_params": []}, "float": {"optional_params": [], "type": "<type 'float'>", "default_params": [], "required_params": []}, "numeric": {"optional_params": [], "type": "<type 'float'>", "default_params": [], "required_params": []}, "int": {"optional_params": [], "type": "<type 'int'>", "default_params": [], "required_params": []}, "categorical_label": {"optional_params": ["split_pattern", "min_df"], "type": "", "default_params": [], "required_params": []}, "boolean": {"optional_params": [], "type": "<type 'bool'>", "default_params": [], "required_params": []}, "date": {"optional_params": [], "type": "", "default_params": [], "required_params": ["pattern"]}}}}
"""
  type: 'json'
  status: 'OK'
  statusCode: 200
,
  key: 'loading examples of a test with paging'
  url_regex: new RegExp '^.+/cloudml/models/888/tests/999/examples/?'
  data: """
{"has_next": true, "test_examples": [{"example_id": "-1", "name": "noname", "title": null, "id": 10959, "label": "True", "pred_label": "False", "prob": [0.619566141782423, 0.380433858217577]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10960, "label": "True", "pred_label": "False", "prob": [0.64064821439669, 0.35935178560331]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10961, "label": "False", "pred_label": "False", "prob": [0.513987966248721, 0.486012033751279]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10962, "label": "True", "pred_label": "False", "prob": [0.568338212873086, 0.431661787126914]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10963, "label": "True", "pred_label": "False", "prob": [0.618320616618649, 0.381679383381351]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10964, "label": "True", "pred_label": "True", "prob": [0.226877614120028, 0.773122385879972]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10965, "label": "False", "pred_label": "False", "prob": [0.509987094329648, 0.490012905670352]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10966, "label": "True", "pred_label": "False", "prob": [0.621967978017825, 0.378032021982175]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10967, "label": "False", "pred_label": "True", "prob": [0.318521150905764, 0.681478849094236]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10968, "label": "True", "pred_label": "True", "prob": [0.212209282811909, 0.787790717188091]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10969, "label": "False", "pred_label": "True", "prob": [0.228424997663939, 0.771575002336061]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10970, "label": "True", "pred_label": "True", "prob": [0.479340413896968, 0.520659586103032]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10971, "label": "True", "pred_label": "True", "prob": [0.424063158430864, 0.575936841569136]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10972, "label": "True", "pred_label": "True", "prob": [0.430397184802764, 0.569602815197236]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10973, "label": "False", "pred_label": "False", "prob": [0.632063693366599, 0.367936306633401]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10974, "label": "True", "pred_label": "True", "prob": [0.391169369802578, 0.608830630197422]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10975, "label": "True", "pred_label": "True", "prob": [0.447260600244514, 0.552739399755486]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10976, "label": "True", "pred_label": "True", "prob": [0.307867862974186, 0.692132137025814]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10977, "label": "True", "pred_label": "True", "prob": [0.399190655108169, 0.600809344891831]}, {"example_id": "-1", "name": "noname", "title": null, "id": 10978, "label": "False", "pred_label": "True", "prob": [0.291823716176112, 0.708176283823888]}], "pages": 174, "has_prev": false, "per_page": 20, "total": 3480, "page": 1}
"""
  type: 'json'
  status: 'OK'
  statusCode: 200
]