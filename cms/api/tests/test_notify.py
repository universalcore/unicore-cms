import os
import pygit2
import shutil
from pyramid import testing
from webtest import TestApp
from cms import main, models
from cms.api.tests.utils import BaseTestCase
from gitmodel.workspace import Workspace


class NotifyTestCase(BaseTestCase):

    def delete_test_repo(self):
        try:
            shutil.rmtree(self.repo_path_remote)
            shutil.rmtree(self.repo_path)
        except:
            pass

    def setup_repositories(self):
        self.repo_remote = pygit2.init_repository(self.repo_path_remote, True)
        author = pygit2.Signature('test', 'test@user.com')
        committer = author
        tree = self.repo_remote.TreeBuilder().write()
        self.repo_remote.create_commit(
            'refs/heads/master',
            author, committer, 'initialize master branch',
            tree,
            []
        )

        # cloning the remote repo will set it up as the upstream
        # changes made to the remote repo can then be pulled by a fastforward
        pygit2.clone_repository(self.repo_path_remote, self.repo_path)

    def get_remote_repo_models(self):
        repo = self.repo_remote
        try:
            ws = Workspace(repo.path, repo.head.name)
        except:
            ws = Workspace(repo.path)

        ws.register_model(models.Page)
        ws.register_model(models.Category)
        return ws.import_models(models)

    def init_remote_categories(self):
        models = self.get_remote_repo_models()

        models.Category(
            title='Diarrhoea', slug='diarrhoea'
        ).save(True, message='added diarrhoea Category')

        models.Category(
            title='Hygiene', slug='hygiene'
        ).save(True, message='added hygiene Category')

    def init_remote_pages(self):
        models = self.get_remote_repo_models()

        models.Page(
            title='Test Page 1', content='this is sample content for pg 1'
        ).save(True, message='added page 1')

        models.Page(
            title='Test Page 2', content='this is sample content for pg 2'
        ).save(True, message='added page 2')

    def setUp(self):
        self.repo_path_remote = os.path.join(os.getcwd(), '.test_remote_repo/')

        self.delete_test_repo()
        self.setup_repositories()

        self.config = testing.setUp()
        settings = {'git.path': self.repo_path, 'CELERY_ALWAYS_EAGER': True}
        self.app = TestApp(main({}, **settings))

        self.init_remote_categories()
        self.init_remote_pages()

    def tearDown(self):
        testing.tearDown()
        self.delete_test_repo()

    def test_fastforward(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 0)
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 0)

        # this should trigger a fastforward
        self.app.post('/api/notify/', status=200)

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)
