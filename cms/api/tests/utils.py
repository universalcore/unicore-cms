import os
import pygit2
import shutil
import unittest

from cms import models as cms_models
from gitmodel.workspace import Workspace


class BaseTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.repo_path = os.path.join(os.getcwd(), '.test_repo/')

    def delete_test_repo(self):
        try:
            shutil.rmtree(self.repo_path)
        except:
            pass

    def get_repo_models(self):
        repo = pygit2.Repository(self.repo_path)
        try:
            ws = Workspace(repo.path, repo.head.name)
        except:
            ws = Workspace(repo.path)

        ws.register_model(cms_models.Page)
        ws.register_model(cms_models.Category)
        return ws.import_models(cms_models)

    def init_categories(self):
        models = self.get_repo_models()

        models.Category(
            title='Diarrhoea', slug='diarrhoea'
        ).save(True, message='added diarrhoea Category')

        models.Category(
            title='Hygiene', slug='hygiene'
        ).save(True, message='added hygiene Category')
