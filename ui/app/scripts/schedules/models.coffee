angular.module('app.schedules.model', ['app.config'])

.factory('Schedule', [
  '$http'
  '$q'
  'settings'
  'BaseModel'
  
  ($http, $q, settings, BaseModel) ->
    ###
    Periodic Task Schedule
    ###
    class Schedule  extends BaseModel
      BASE_API_URL: "#{settings.apiUrl}schedules/"
      BASE_UI_URL: '/schedules'
      API_FIELDNAME: 'schedule'
      DEFAULT_FIELDS_TO_SAVE: ['name', 'descriptions', 'scenarios', 'interval',
                               'enabled', 'crontab', 'type']
      @MAIN_FIELDS: ['id','name','created_on','updated_on','enabled','descriptions',
                    'scenarios','interval','crontab','created_by','type','status'].join(',')

      @LIST_MODEL_NAME: 'schedules'
      LIST_MODEL_NAME: @LIST_MODEL_NAME
      SCHEDULE_TYPES: ['crontab', 'interval']
      CRONTAB_CONFIG: [{name: 'minute', type: 'string', default: '*'},
                       {name: 'hour', type: 'string', default: '*'},
                       {name: 'day_of_week', type: 'string', default: '*'},
                       {name: 'day_of_month', type: 'string', default: '*'},
                       {name: 'month_of_year', type: 'string', default: '*'}]
      INTERVAL_CONFIG: [{name:'every', type: 'integer'},
                        {name: 'period', type: 'string', choices: ['microseconds', 'seconds', 'minutes', 'hours', 'days']}]
      TASK_TYPES: ['single', 'chain', 'chord', 'group']
      TASK_CONFIG: [
        {
            'task': 'api.import_handlers.tasks.create_dataset',
            'params': [{'name': 'import_handler_id', 'type': 'integer', 'entity': 'XmlImportHandler'},
                       {'name': 'import_params', 'type': 'string', 'entity': 'InputParameter', 'dependency': 'import_handler_id', 'dict_fields': true, 'add_info': ['type', 'regex', 'format']},
                       {'name': 'data_format', 'type': 'string', 'choices': ['json', 'csv'], 'default': 'json'}],
            'result': ['dataset_ids']
        },
        {
            'task': 'api.import_handlers.tasks.import_data',
            'params': [{'name': 'import_handler_id', 'type': 'integer', 'entity': 'XmlImportHandler'},
                       {'name': 'dataset_id', 'type': 'integer', 'entity': 'DataSet', 'dependency': 'import_handler_id'}],
            'result': ['dataset_ids']
        },
        {
            'task': 'api.import_handlers.tasks.upload_dataset',
            'params': [{'name': 'import_handler_id', 'type': 'integer', 'entity': 'XmlImportHandler'},
                       {'name': 'dataset_id', 'type': 'integer', 'entity': 'DataSet', 'dependency': 'import_handler_id'}],
            'result': ['dataset_ids']
        },
        #{
        #    'task': 'api.import_handlers.tasks.load_pig_fields',
        #    'params': [{'name': 'import_handler_id', 'type': 'integer', 'entity': 'XmlImportHandler'},
        #               {'name': 'entity_id', 'type': 'integer', 'entity': 'XmlEntity', 'dependency': 'import_handler_id'},
        #               {'name': 'sqoop_id', 'type': 'integer', 'entity': 'XmlSqoop', 'dependency': 'import_handler_id'},
        #               {'name': 'params', 'type': 'string'}],
        #    'result': ['fields', 'sample', 'sql']
        #},
        {
            'task': 'api.instances.tasks.synchronyze_cluster_list',
            'params': [],
            'result': []
        },
        #{
        #    'task': 'api.instances.tasks.request_spot_instance',
        #    'params': [{'name': 'instance_type', 'type': 'choices','choices': ['m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge', 'hi1.4xlarge', 'hs1.8xlarge']},
        #               {'name': 'model_id', 'type': 'integer', 'entity': 'Model'}],
        #    'result': ['request_id']
        #},
        {
            'task': 'api.ml_models.tasks.models.train_model',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model', 'add_info': ['train_import_handler_id']},
                        {'name': 'dataset_ids', 'type': 'string', 'entity': 'DataSet', 'dependency': 'import_handler_id', 'choose_multiple': true}],
            'result': []
        },
        {
            'task': 'api.ml_models.tasks.models.train_model_request_instance',
            'params': [{'name': 'instance_type', 'type': 'choices', 'choices': ['m3.xlarge', 'm3.2xlarge', 'cc2.8xlarge', 'cr1.8xlarge', 'hi1.4xlarge', 'hs1.8xlarge']}
                       {'name': 'model_id', 'type': 'integer', 'entity': 'Model', 'add_info': ['train_import_handler_id']},
                       {'name': 'dataset_ids', 'type': 'string','entity': 'DataSet', 'dependency': 'import_handler_id','choose_multiple': true}],
            'result': []
        },
        #{
        #    'task': 'api.instances.tasks.cancel_request_spot_instance',
        #    'params': [{'name': 'request_id', 'type': 'string'},
        #               {'name': 'model_id', 'type': 'integer', 'entity': 'Model'}],
        #    'result': []
        #},
        #{
        #    'task': 'api.instances.tasks.self_terminate',
        #    'params': [],
        #    'result': []
        #},
        {
            'task': 'api.instances.tasks.run_ssh_tunnel',
            'params': [{'name': 'cluster_id', 'type': 'integer','entity': 'Cluster'}],
            'result': []
        },
        #{
        #    'task': 'api.ml_models.tasks.models.get_classifier_parameters_grid',
        #    'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
        #               {'name': 'grid_params_id', 'type': 'integer', 'entity': 'ClassifierGridParams'}],
        #    'result': []
        #},
        {
            'task': 'api.ml_models.tasks.models.visualize_model',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
                       {'name': 'segment_id', 'type': 'integer', 'entity': 'Segment', 'dependency': 'model_id'}],
            'result': []
        },
        {
            'task': 'api.ml_models.tasks.models.generate_visualization_tree',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
                       {'name': 'deep', 'type': 'integer'}],
            'result': []
        },
        {
            'task': 'api.ml_models.tasks.models.transform_dataset_for_download',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model','add_info': ['train_import_handler_id']},
                       {'name': 'dataset_id', 'type': 'integer', 'entity': 'DataSet', 'dependency': 'import_handler_id'}],
            'result': ['s3_download_url']
        },
        {
            'task': 'api.ml_models.tasks.models.upload_segment_features_transformers',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
                       {'name': 'segment_id', 'type': 'integer','entity': 'Segment', 'dependency': 'model_id'},
                       {'name': 'fformat', 'type': 'choices', 'choices': ['json', 'csv']}],
            'result': ['s3_download_url']
        },
        {
            'task': 'api.ml_models.tasks.models.clear_model_data_cache',
            'params': [],
            'result': []
        },
        {
            'task': 'api.ml_models.tasks.models.calculate_model_parts_size',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
                       {'name': 'deep', 'type': 'integer', 'default': 7}],
            'result': []
        },
        {
            'task': 'api.ml_models.tasks.transformers.train_transformer',
            'params': [{'name': 'transformer_id', 'type': 'integer', 'entity': 'Transformer', 'add_info': ['train_import_handler_id']}
                       {'name': 'dataset_ids', 'type': 'string','entity': 'DataSet', 'dependency': 'import_handler_id', 'choose_multiple': true}],
            'result': []
        },
        {
            'task': 'api.model_tests.tasks.test_model',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model', 'add_info': ['test_import_handler_id']},
                       {'name': 'dataset_ids', 'type': 'string', 'entity': 'DataSet', 'dependency': 'import_handler_id', 'choose_multiple': true}],
            'result': ['test_id']
        },
        {
            'task': 'api.model_tests.tasks.calculate_confusion_matrix',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model', 'add_info': ['labels']},
                       {'name': 'test_id', 'type': 'integer', 'entity': 'TestResult', 'dependency': 'model_id'},
                       {'name': 'weights', 'type': 'string', 'dependency': 'model_id', 'dict_fields': true, 'entity': 'Mock', 'mocked': 'labels'}],
            'result': ['confusion_matrix']
        },
        #{
        #    'task': 'api.model_tests.tasks.export_results_to_db',
        #    'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
        #               {'name': 'test_id', 'type': 'integer',
        #                'entity': 'TestResult'},
        #               {'name': 'datasource_id', 'type': 'integer',
        #                'entity': 'XmlDataSource'},
        #               {'name': 'table_name', 'type': 'string'},
        #               {'name': 'fields', 'type': 'string'}],
        #    'result': []
        #},
        {
            'task': 'api.model_tests.tasks.get_csv_results',
            'params': [{'name': 'model_id', 'type': 'integer', 'entity': 'Model'},
                       {'name': 'test_id', 'type': 'integer', 'entity': 'TestResult', 'dependency': 'model_id'},
                       {'name': 'fields', 'type': 'string'}],
            'result': ['s3_download_url']
        },
        {
            'task': 'api.servers.tasks.upload_model_to_server',
            'params': [{'name': 'server_id', 'type': 'integer', 'entity': 'Server'},
                       {'name': 'model_id', 'type': 'integer', 'entity': 'Model'}],
            'result': ['file_name']
        },
        {
            'task': 'api.servers.tasks.upload_import_handler_to_server',
            'params': [{'name': 'server_id', 'type': 'integer', 'entity': 'Server'},
                       {'name': 'handler_type', 'type': 'choices', 'choices': ['xml']},
                       {'name': 'import_handler_id', 'type': 'integer', 'entity': 'XmlImportHandler'}],
            'result': ['file_name']
        },
        {
            'task': 'api.servers.tasks.update_at_server',
            'params': [{'name': 'file_name', 'type': 'string'},
                       {'name': 'server_id', 'type': 'integer', 'entity': 'Server'}],
            'result': []
        },
        {
            'task': 'api.servers.tasks.verify_model',
            'params': [{'name': 'verification_id', 'type': 'integer', 'entity': 'ModelVerification'},
                       {'name': 'count', 'type': 'integer'}],
            'result': []
        }
      ]

      id: null
      name: null
      scenariosDict: []
      intervalDict: {}
      crontabDict: {}

      loadFromJSON: (origData) =>
        super origData
        if origData?
          if origData.scenarios?
            @scenariosDict.splice(0, @scenariosDict.length)
            @scenariosDict.push origData['scenarios']
          if origData.interval?
            @intervalDict = origData['interval']
          if origData.crontab?
            @crontabDict = origData['crontab']


      $save: (opts={}) =>
        if opts.only? && "interval" in opts.only
          if @type == 'crontab'
            @intervalDict = {}
          @interval = JSON.stringify(@intervalDict)

        if opts.only? && "crontab" in opts.only
          if @type == 'interval'
            @crontabDict = {}
          @crontab = JSON.stringify(@crontabDict)

        if opts.only? && "scenarios" in opts.only
          @scenarios = JSON.stringify(@scenariosDict[0])

        super opts


    return Schedule
])