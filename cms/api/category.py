import os
import pygit2

from cornice.resource import resource, view

from cms import models as cms_models
from cms.api import validators
from gitmodel.workspace import Workspace
from gitmodel.exceptions import DoesNotExist



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


@resource(
    collection_path='/api/categories.json',
    path='/api/categories/{uuid}.json'
)
class CategoryApi(object):

    def __init__(self, request):
        self.request = request

    def collection_get(self):
        models = get_repo_models(self.request)
        return [c.to_dict() for c in models.Category().all()]

    @view(renderer='json')
    def get(self):
        models = get_repo_models(self.request)
        uuid = self.request.matchdict['uuid']
        try:
            category = models.Category().get(uuid)
            return category.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_post_category, renderer='json')
    def post(self):
        uuid = self.request.matchdict['uuid']
        title = self.request.validated['title']

        models = get_repo_models(self.request)
        try:
            category = models.Category().get(uuid)
            category.title = title
            category.save(True, message='Category updated: %s' % title)
            get_registered_ws(self.request).sync_repo_index()
            return category.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_put_category, renderer='json')
    def collection_put(self):
        title = self.request.validated['title']

        models = get_repo_models(self.request)
        try:
            category = models.Category(title=title)
            category.save(True, message='Category added: %s' % title)
            get_registered_ws(self.request).sync_repo_index()
            return category.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')
            return

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        models = get_repo_models(self.request)
        try:
            category = models.Category().get(uuid)
            models.Category.delete(
                uuid, True, message='Category delete: %s' % category.title)
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')
