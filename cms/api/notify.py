from cornice.resource import resource
from cms.api.base import ApiBase
from unicore.distribute.tasks import fastforward


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def post(self):
        fastforward.delay(
            self.settings['git.path'],
            self.settings['es.index_prefix'])
        return {}
