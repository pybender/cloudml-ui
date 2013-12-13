import json

from fixture import DataSet


class ImportHandlerData(DataSet):
    class import_handler_01:
        name = "Handler 1"
        type = "Db"
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        import_params = ['start', 'end', 'category']
        data = json.loads("""
        {
  "target-schema":"bestmatch",
  "datasource":[
    {
      "name":"odw",
      "type":"sql",
      "db":{
        "conn":"host='localhost' dbname='cloudml' user='cloudml' password='cloudml'",
        "vendor":"postgres"
      }
    }
  ],
  "queries":[
    {
      "name":"retrieve",
      "sql": "SELECT qi.*, 'class' || (trunc(random() * 2) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);",
      "items": [
        {
          "name":"odw",
          "type":"sql",
          "db":{
            "conn":"host='localhost' dbname='cloudml' user='cloudml' password='cloudml'",
            "vendor":"postgres"
          }
        }
      ],
      "queries":[
        {
          "name":"retrieve",
          "sql": "SELECT qi.*, 'class' || (trunc(random() * 2) + 1)::char hire_outcome FROM public.ja_quick_info qi where qi.file_provenance_date >= '%(start)s' AND qi.file_provenance_date < '%(end)s' LIMIT(100);",
          "items": [
            {
              "source": "application",
              "process_as": "string",
              "is_required": true,
              "target_features": [
                { "name": "application_id" }
              ]
            },
            {
              "source": "opening",
              "process_as": "string",
              "is_required": true,
              "target_features": [
                { "name": "opening_id" }
              ]
            },
            {
              "source": "hire_outcome",
              "process_as": "string",
              "is_required": true,
              "target_features": [
                { "name": "hire_outcome" }
              ]
            },
            { "source": "employer_info",
              "is_required": true,
              "process_as": "json",
              "target_features": [
                { "name": "employer.op_timezone", "jsonpath": "$.op_timezone"},
                { "name": "employer.op_country_tz", "jsonpath": "$.op_country_tz" },
                { "name": "employer.op_tot_jobs_filled", "jsonpath": "$.op_tot_jobs_filled" },
                { "name": "employer.country", "jsonpath": "$.op_country" }
              ]
            },
            { "source": "contractor_info",
              "is_required": true,
              "process_as": "json",
              "target_features": [
                { "name": "contractor.skills", "jsonpath": "$.skills.*.skl_name", "to-csv": true},
                { "name": "tsexams", "jsonpath": "$.tsexams", "key_path": "$.*.ts_name", "value_path": "$.*.ts_score" },
                { "name": "contractor.dev_adj_score_recent", "jsonpath": "$.dev_adj_score_recent"},
                { "name": "contractor.dev_is_looking", "jsonpath": "$.dev_is_looking" },
                { "name": "contractor.dev_recent_rank_percentile", "jsonpath": "$.dev_recent_rank_percentile" },
                { "name": "contractor.dev_recent_fp_jobs", "jsonpath": "$.dev_recent_fp_jobs" },
                { "name": "contractor.dev_recent_hours", "jsonpath": "$.dev_recent_hours" },
                { "name": "contractor.dev_skill_test_passed_count", "jsonpath": "$.dev_skill_test_passed_count" },
                { "name": "contractor.dev_total_hourly_jobs", "jsonpath": "$.dev_total_hourly_jobs" },
                { "name": "contractor.dev_tot_feedback_recent", "jsonpath": "$.dev_tot_feedback_recent" },
                { "name": "contractor.dev_rank_percentile", "jsonpath": "$.dev_rank_percentile" },
                { "name": "contractor.dev_billed_assignments", "jsonpath": "$.dev_billed_assignments" },
                { "name": "contractor.dev_is_looking_week", "jsonpath": "$.dev_is_looking_week" },
                { "name": "contractor.dev_availability", "jsonpath": "$.dev_availability" },
                { "name": "contractor.dev_total_revenue", "jsonpath": "$.dev_total_revenue" },
                { "name": "contractor.dev_bill_rate", "jsonpath": "$.dev_bill_rate" },
                { "name": "contractor.dev_test_passed_count", "jsonpath": "$.dev_test_passed_count" },
                { "name": "contractor.dev_expose_full_name", "jsonpath": "$.dev_expose_full_name" },
                { "name": "contractor.dev_total_hours_rounded", "jsonpath": "$.dev_total_hours_rounded" },
                { "name": "contractor.dev_year_exp", "jsonpath": "$.dev_year_exp" },
                { "name": "contractor.dev_portfolio_items_count", "jsonpath": "$.dev_portfolio_items_count" },
                { "name": "contractor.dev_eng_skill", "jsonpath": "$.dev_eng_skill" },
                { "name": "contractor.dev_tot_feedback", "jsonpath": "$.dev_tot_feedback" },
                { "name": "contractor.dev_timezone", "jsonpath": "$.dev_timezone" },
                { "name": "contractor.dev_last_worked", "jsonpath": "$.dev_last_worked" },
                { "name": "contractor.dev_profile_title", "jsonpath": "$.dev_profile_title" },
                { "name": "contractor.dev_active_interviews", "jsonpath": "$.dev_active_interviews" },
                { "name": "contractor.dev_cur_assignments", "jsonpath": "$.dev_cur_assignments" },
                { "name": "contractor.dev_pay_rate", "jsonpath": "$.dev_pay_rate" },
                { "name": "contractor.dev_blurb", "jsonpath": "$.dev_blurb" },
                { "name": "contractor.dev_country", "jsonpath": "$.dev_country" }
              ]
            },
            {
              "process_as": "composite",
              "target_features": [
                { "name": "country_pair", "expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}}
              ]
            }
          ]
        }
      ]
    }
  ]
}
""")


class DataSetData(DataSet):
    class dataset_01:
        name = "DS"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "5270dd3a106a6c1631000000.json"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/ds.gz"
        filesize = 100
        records_count = 100
        time = 200
        data_fields = ["employer.country"]
        format = "json"
        import_handler_id = ImportHandlerData.import_handler_01.ref('id')

    class dataset_02:
        name = "DS 2"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "5270dd3a106a6c1631000000.json"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/ds2.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "json"
        import_handler_id = ImportHandlerData.import_handler_01.ref('id')

    class dataset_03:
        name = "DS 3 (csv)"
        status = "Importing"
        error = ""
        created_on = "2013-04-19 14:37:23.145000"
        updated_on = "2013-04-19 14:37:23.145000"
        data = "5270dd3a106a6c1631000000.csv"
        import_params = '{}'
        on_s3 = False
        compress = True
        filename = "api/import_handlers/ds_csv.gz"
        filesize = 100
        records_count = 100
        time = 200
        format = "csv"
        import_handler_id = ImportHandlerData.import_handler_01.ref('id')
