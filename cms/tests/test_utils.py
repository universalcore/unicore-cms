from unittest import TestCase

from cms.utils import get_workspace, WORKSPACE_CACHE
from cms.tests.utils import RepoHelper


class TestUtils(TestCase):

    maxDiff = None

    def test_get_worspace_caching(self):

        repo_helper = RepoHelper.create('../.workspace_test')
        self.addCleanup(repo_helper.destroy)

        repo = repo_helper.repo
        workspace1 = get_workspace(repo)
        workspace2 = get_workspace(repo)
        self.assertEqual(workspace1, workspace2)
