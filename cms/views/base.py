from elasticgit import EG


class BaseCmsView(object):

    def __init__(self, request):
        self.request = request
        self.locale = request.locale_name
        self.settings = request.registry.settings
        self.workspace = EG.workspace(
            workdir=self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'])
