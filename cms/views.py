import os
from gitmodel.workspace import Workspace
from pyramid.view import view_config
from cms import models as cms_models


@view_config(route_name='home', renderer='templates/home.pt')
def my_view(request):
    repo_path = os.path.join(request.registry.settings['git.path'], '.git')
    ws = Workspace(repo_path)
    models = ws.import_models(cms_models)
    categories = models.Category().all()
    return {'categories': categories}
