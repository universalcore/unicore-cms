import os
from unittest import TestCase

from cms.utils import get_workspace
from cms.tests.utils import RepoHelper


class TestUtils(TestCase):

    def test_get_worspace_caching(self):

        repo_helper = RepoHelper.create(
            os.path.join(os.getcwd(), '.workspace_test'))
        self.addCleanup(repo_helper.destroy)

        repo = repo_helper.repo
        workspace1 = get_workspace(repo)
        workspace2 = get_workspace(repo)
        self.assertEqual(workspace1, workspace2)
