import os

from cms.tests.utils import BaseTestCase, RepoHelper


class ApiBaseTestCase(BaseTestCase):

    def __init__(self, *args, **kwargs):
        super(ApiBaseTestCase, self).__init__(*args, **kwargs)
        self.repo_path = os.path.join(os.getcwd(), '.test_repo/')
        self.repo_helper = RepoHelper(self.repo_path)
