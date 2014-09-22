import os
import pygit2
import shutil
import unittest

from unicore_gitmodels import models
from cms import utils


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
        ws = utils.get_workspace(repo)
        ws.register_model(models.GitPageModel)
        ws.register_model(models.GitCategoryModel)
        return ws.import_models(models)

    def init_categories(self):
        models = self.get_repo_models()

        models.GitCategoryModel(
            title='Diarrhoea', slug='diarrhoea'
        ).save(True, message='added diarrhoea Category')

        models.GitCategoryModel(
            title='Hygiene', slug='hygiene'
        ).save(True, message='added hygiene Category')

    def init_pages(self):
        models = self.get_repo_models()

        models.GitPageModel(
            title='Test Page 1', content='this is sample content for pg 1'
        ).save(True, message='added page 1')

        models.GitPageModel(
            title='Test Page 2', content='this is sample content for pg 2'
        ).save(True, message='added page 2')
