import os
from pyramid import testing
from webtest import TestApp
from cms import main
from cms.tests.utils import BaseTestCase, RepoHelper


class NotifyTestCase(BaseTestCase):

    def setUp(self):
        self.repo_path = os.path.join(
            os.getcwd(), '.test_repos', self.id())

        self.repo_path_remote = os.path.join(
            os.getcwd(), '.test_remote_repos', self.id())
        self.remote_repo = RepoHelper.create(self.repo_path_remote)

        self.config = testing.setUp()
        settings = {
            'git.path': self.repo_path,
            'git.content_repo_url': self.remote_repo.workdir,
            'CELERY_ALWAYS_EAGER': True
        }
        self.app = TestApp(main({}, **settings))

    def tearDown(self):
        self.remote_repo.destroy()
        RepoHelper.read(self.repo_path).destroy()
        testing.tearDown()

    def test_fastforward(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 0)
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 0)

        # the remote grows some categories
        self.remote_repo.create_categories()
        self.remote_repo.create_pages()

        # this should trigger a fastforward
        self.app.post('/api/notify/', status=200)

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)
