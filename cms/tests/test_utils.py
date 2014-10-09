import os
from unittest import TestCase

from cms.tests.utils import RepoHelper


class TestUtils(TestCase):

    def test_get_worspace_caching(self):

        repo_helper = RepoHelper.create(
            os.path.join(os.getcwd(), '.workspace_test', self.id()))
        self.addCleanup(repo_helper.destroy)

        workspace1 = repo_helper.get_workspace()
        workspace2 = repo_helper.get_workspace()
        self.assertEqual(workspace1, workspace2)
        self.assertTrue(repo_helper in RepoHelper.WORKSPACE_CACHE.values())
