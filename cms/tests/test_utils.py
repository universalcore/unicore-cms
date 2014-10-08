from unittest import TestCase

from cms.utils import get_workspace, WORKSPACE_CACHE
from cms.tests.utils import RepoHelper


class TestUtils(TestCase):

    def setUp(self):
        self.repo_helper = RepoHelper.create('.workspace_test')
        self.repo = self.repo_helper.repo

    def tearDown(self):
        self.repo_helper.destroy()

    def test_get_worspace_caching(self):
        self.assertEqual(WORKSPACE_CACHE, {})
        workspace1 = get_workspace(self.repo)
        workspace2 = get_workspace(self.repo)
        self.assertEqual(WORKSPACE_CACHE.keys(), [self.repo.path])
        self.assertEqual(workspace1, workspace2)
