import os
import pygit2

from cornice import Service
from cms import models as cms_models
from gitmodel.workspace import Workspace
from gitmodel.exceptions import DoesNotExist

category_service = Service(
    name='category_service',
    path='/api/categories.json',
    description="Manage categories"
)


def get_repo_models(request):
    repo_path = os.path.join(request.registry.settings['git.path'], '.git')
    repo = pygit2.Repository(repo_path)
    try:
        ws = Workspace(repo.path, repo.head.name)
    except:
        ws = Workspace(repo.path)

    ws.register_model(cms_models.Page)
    ws.register_model(cms_models.Category)
    return ws.import_models(cms_models)


@category_service.get()
def get_categories(request):
    models = get_repo_models(request)

    uuid = request.GET.get('uuid', None)
    if uuid:
        try:
            category = models.Category().get(uuid)
            return category.to_dict()
        except DoesNotExist:
            request.errors.add('api', 'DoesNotExist', 'Category not found.')
            return
    return [c.to_dict() for c in models.Category().all()]
