import os
import pygit2

from cornice import Service
from cms import models as cms_models
from cms.api import validators
from gitmodel.workspace import Workspace
from gitmodel.exceptions import DoesNotExist

category_service = Service(
    name='category_service',
    path='/api/categories.json',
    description="Manage categories"
)


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


@category_service.post(validators=validators.validate_post_category)
def post_category(request):
    uuid = request.validated['uuid']
    title = request.validated['title']

    models = get_repo_models(request)
    if uuid:
        try:
            category = models.Category().get(uuid)
            category.title = title
            category.save(True, message='Category updated: %s' % title)
            get_registered_ws(request).sync_repo_index()
            return {'success': True}
        except DoesNotExist:
            request.errors.add('api', 'DoesNotExist', 'Category not found.')
            return


@category_service.put(validators=validators.validate_put_category)
def put_category(request):
    # TODO - raise exception when duplicate category is posted

    title = request.validated['title']

    models = get_repo_models(request)
    category = models.Category(title=title)
    category.save(True, message='Category added: %s' % title)
    get_registered_ws(request).sync_repo_index()
    return category.to_dict()


@category_service.delete(validators=validators.validate_delete_category)
def delete_category(request):
    uuid = request.GET.get('uuid')
    models = get_repo_models(request)
    try:
        category = models.Category().get(uuid)
        models.Category.delete(
            uuid, True, message='Category delete: %s' % category.title)
        return {'success': True}
    except DoesNotExist:
        request.errors.add('api', 'DoesNotExist', 'Category not found.')
