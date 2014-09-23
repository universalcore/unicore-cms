import os
from pyramid import testing

from cms.views import CmsViews
from cms.tests.utils import BaseTestCase, RepoHelper


class TestViews(BaseTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.repo = RepoHelper.create(os.path.join(os.getcwd(), '.test_repo'))
        self.config = testing.setUp(settings={
            'git.path': self.repo.path,
            'git.content_repo_url': '',
        })
        self.views = CmsViews({}, testing.DummyRequest())

    def tearDown(self):
        self.repo.destroy()
        testing.tearDown()

    def test_get_pages_count(self):
        self.repo.create_pages(count=10)
        pages = self.views.get_pages(limit=7)
        self.assertEqual(len(pages), 7)
