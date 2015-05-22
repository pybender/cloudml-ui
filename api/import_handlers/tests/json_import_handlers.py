import uuid
import json
from datetime import datetime

from mock import patch, MagicMock
from moto import mock_s3
from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from api.import_handlers.views import ImportHandlerResource
from api.import_handlers.models import ImportHandler
from api.servers.fixtures import ServerData

AUTH_TOKEN = 'token'
HTTP_HEADERS = [('X-Auth-Token', AUTH_TOKEN)]


class ImportHandlerResourceTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the XML ImportHandlers API.
    """
    BASE_URL = '/cloudml/importhandlers/'
    RESOURCE = ImportHandlerResource
    Model = ImportHandler
    datasets = [ServerData]

    def setUp(self):
        super(ImportHandlerResourceTests, self).setUp()
        name = str(uuid.uuid1())
        with open('conf/extract.json', 'r') as fp:
            resp_data = self._check(method='post', data={
                'name': name,
                'data': fp.read()
            })
        self.assertEqual(resp_data[self.RESOURCE.OBJECT_NAME]['name'], name)
        self.obj = self.Model.query.filter_by(name=name).first()
        self.assertEqual(set(['start', 'end']), set(self.obj.import_params))

    def test_list(self):
        self.check_list(show='name,import_params')

    def test_get_list_fields(self):
        url = self._get_url(id=self.obj.id, action='list_fields')

        resp = self.client.get(url, headers=HTTP_HEADERS)
        resp_obj = json.loads(resp.data)
        self.assertTrue('fields' in resp_obj)
        self.assertEqual(39, len(resp_obj['fields']))


class ImportHandlerModelTests(BaseDbTestCase):

    def test_list_fields(self):
        data = open('conf/extract.json', 'r').read()
        handler = ImportHandler(name='json ih', data=json.loads(data))
        handler.save()
        fields = handler.list_fields()
        self.assertEqual(39, len(fields))
        self.assertEqual(
            ['application_id', 'opening_id', 'hire_outcome',
             'employer.op_timezone', 'employer.op_country_tz',
             'employer.op_tot_jobs_filled', 'employer.country',
             'contractor.skills', 'tsexams', 'contractor.dev_adj_score_recent',
             'contractor.dev_is_looking',
             'contractor.dev_recent_rank_percentile',
             'contractor.dev_recent_fp_jobs',
             'contractor.dev_recent_hours',
             'contractor.dev_skill_test_passed_count',
             'contractor.dev_total_hourly_jobs',
             'contractor.dev_tot_feedback_recent',
             'contractor.dev_rank_percentile',
             'contractor.dev_billed_assignments',
             'contractor.dev_is_looking_week',
             'contractor.dev_availability',
             'contractor.dev_total_revenue', 'contractor.dev_bill_rate',
             'contractor.dev_test_passed_count',
             'contractor.dev_expose_full_name',
             'contractor.dev_total_hours_rounded',
             'contractor.dev_year_exp', 'contractor.dev_portfolio_items_count',
             'contractor.dev_eng_skill', 'contractor.dev_tot_feedback',
             'contractor.dev_timezone', 'contractor.dev_last_worked',
             'contractor.dev_profile_title',
             'contractor.dev_active_interviews',
             'contractor.dev_cur_assignments', 'contractor.dev_pay_rate',
             'contractor.dev_blurb', 'contractor.dev_country', 'country_pair'],
            fields)
