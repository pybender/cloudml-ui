from api.base.test_utils import BaseDbTestCase, TestChecksMixin
from ..views import TagResource
from ..fixtures import TagData
from ..models import Tag


class TagsTests(BaseDbTestCase, TestChecksMixin):
    """
    Tests of the Tags API.
    """
    BASE_URL = '/cloudml/tags/'
    RESOURCE = TagResource
    datasets = [TagData, ]
    Model = Tag

    def test_list(self):
        resp = self.check_list(show='text,count')
        tag = resp['tags'][0]
        self.assertEquals(tag['text'], TagData.tag_01.text)
        self.assertEquals(tag['count'], TagData.tag_01.count)
        self.assertEquals(len(tag.keys()), 3)  # id also
