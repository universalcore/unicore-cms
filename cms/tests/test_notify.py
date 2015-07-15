from pyramid import testing

from elasticgit import EG
from unicore.content.models import Page, Category, Localisation

from cms.tests.base import UnicoreTestCase


class NotifyTestCase(UnicoreTestCase):

    def setUp(self):
        self.remote_workspace = self.mk_workspace(
            name='%s_remote' % (self.id().lower(),))
        # there needs to be an initial commit for diffs to work
        index = self.remote_workspace.repo.index
        index.commit('Initial Commit')
        # cloning ensures initial commit is on both and sets up remote
        EG.clone_repo(
            repo_url=self.remote_workspace.repo.working_dir,
            workdir='.test_repos/%s' % self.id().lower())
        self.local_workspace = self.mk_workspace(name=self.id().lower())
        self.config = testing.setUp()
        self.app = self.mk_app(self.local_workspace)

    def tearDown(self):
        testing.tearDown()

    def test_api_notify(self):
        # the remote grows some categories
        self.create_categories(self.remote_workspace)
        self.create_pages(self.remote_workspace)
        self.create_localisation(self.remote_workspace)

        # this should trigger a fastforward
        self.app.post('/api/notify/', status=200)

        self.local_workspace.refresh_index()
        self.assertEquals(self.local_workspace.S(Page).count(), 2)
        self.assertEquals(self.local_workspace.S(Category).count(), 2)
        self.assertEquals(self.local_workspace.S(Localisation).count(), 1)
