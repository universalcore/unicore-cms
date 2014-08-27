import os
import pygit2

from cms import models as cms_models
from gitmodel.workspace import Workspace


def get_registered_ws(request):
    repo_path = os.path.join(request.registry.settings['git.path'], '.git')
    repo = pygit2.Repository(repo_path)
    try:
        ws = Workspace(repo.path, repo.head.name)
    except:
        ws = Workspace(repo.path)

    ws.register_model(cms_models.Page)
    ws.register_model(cms_models.Category)
    return ws


def get_repo_models(request):
    ws = get_registered_ws(request)
    return ws.import_models(cms_models)
