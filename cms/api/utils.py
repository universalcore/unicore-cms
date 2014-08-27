import os
import pygit2

from cms import models as cms_models
from gitmodel.workspace import Workspace


class ApiBase(object):

    def __init__(self, request):
        self.request = request

    def get_registered_ws(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        repo = pygit2.Repository(repo_path)
        try:
            ws = Workspace(repo.path, repo.head.name)
        except:
            ws = Workspace(repo.path)

        ws.register_model(cms_models.Page)
        ws.register_model(cms_models.Category)
        return ws

    def get_repo_models(self):
        ws = self.get_registered_ws()
        return ws.import_models(cms_models)
