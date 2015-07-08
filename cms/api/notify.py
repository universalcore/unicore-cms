from cornice.resource import resource

from cms.api.base import ApiBase
from cms.tasks import pull


@resource(path='/api/notify/')
class NotifyApi(ApiBase):

    def post(self):
        es_host = self.settings.get('es.host', 'http://localhost:9200')
        pull.delay(
            self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'],
            es={'urls': [es_host]})
        return {}
