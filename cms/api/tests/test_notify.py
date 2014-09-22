import os
import pygit2
import shutil
from pyramid import testing
from webtest import TestApp
from unicore_gitmodels import models
from cms import main, utils
from cms.api.tests.utils import BaseTestCase


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

    def get_remote_repo_models(self):
        repo = self.repo_remote
        ws = utils.get_workspace(repo)
        ws.register_model(models.GitPageModel)
        ws.register_model(models.GitCategoryModel)
        return ws.import_models(models)

    def init_remote_categories(self):
        models = self.get_remote_repo_models()

        models.GitCategoryModel(
            title='Diarrhoea', slug='diarrhoea'
        ).save(True, message='added diarrhoea Category')

        models.GitCategoryModel(
            title='Hygiene', slug='hygiene'
        ).save(True, message='added hygiene Category')

    def init_remote_pages(self):
        models = self.get_remote_repo_models()

        models.GitPageModel(
            title='Test Page 1', content='this is sample content for pg 1'
        ).save(True, message='added page 1')

        models.GitPageModel(
            title='Test Page 2', content='this is sample content for pg 2'
        ).save(True, message='added page 2')

    def setUp(self):
        self.repo_path_remote = os.path.join(os.getcwd(), '.test_remote_repo/')

        self.delete_test_repo()
        self.setup_repositories()

        self.config = testing.setUp()
        settings = {
            'git.path': self.repo_path,
            'git.content_repo_url': self.repo_path_remote,
            'CELERY_ALWAYS_EAGER': True
        }
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
