from cornice.resource import resource
from cms.api.base import ApiBase
from unicore.distribute.tasks import fastforward


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def post(self):
        es_host = self.settings.get('es.host', 'http://localhost:9200')
        fastforward.delay(
            self.settings['git.path'],
            self.settings['es.index_prefix'],
            es={'urls': [es_host]})
        return {}
