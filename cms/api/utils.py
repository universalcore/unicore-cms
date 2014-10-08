import pygit2

from unicore_gitmodels import models
from cms import utils


class ApiBase(object):

    def __init__(self, request):
        self.request = request

    def get_registered_ws(self):
        repo_path = self.request.registry.settings['git.path']
        repo = pygit2.Repository(repo_path)
        ws = utils.get_workspace(repo)
        ws.register_model(models.GitPageModel)
        ws.register_model(models.GitCategoryModel)
        return ws

    def get_repo_models(self):
        ws = self.get_registered_ws()
        return ws.import_models(models)
