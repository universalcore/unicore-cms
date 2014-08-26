import os
import shutil
import unittest

from pyramid import testing
from webtest import TestApp
from cms import main


class ViewTests(unittest.TestCase):
    def delete_test_repo(self):
        try:
            shutil.rmtree(self.repo_path)
        except:
            pass

    def setUp(self):
        self.config = testing.setUp()
        self.delete_test_repo()
        self.repo_path = os.path.join(os.getcwd(), '.test_repo/')
        settings = {'git.path': self.repo_path}
        self.app = TestApp(main({}, **settings))

    def tearDown(self):
        testing.tearDown()
        self.delete_test_repo()

    def test_get_categories(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)
