from cornice.resource import resource
from cms.api.base import ApiBase
from cms.tasks import fastforward


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def post(self):
        cb = (fastforward
              if 'sync' in self.request.GET
              else fastforward.delay)
        cb(self.settings['git.path'], self.settings['es.index_prefix'])
        return {}
