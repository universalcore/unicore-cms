import os
from cornice.resource import resource
from cms.api.utils import ApiBase
from cms.tasks import fastforward


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def post(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        fastforward.delay(repo_path)
        return {}
