import pygit2
import os

from cornice.resource import resource
from cms.api.utils import ApiBase
from cms import utils


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def get(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        repo = pygit2.Repository(repo_path)
        try:
            repo = pygit2.Repository(repo_path)
            utils.fast_forward(repo)
        except Exception, e:
            self.request.errors.add('body', 'notify', e.message)
        return {}
