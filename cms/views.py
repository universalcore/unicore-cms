import os
import pygit2

from beaker.cache import cache_region
from cms import models as cms_models
from gitmodel.workspace import Workspace

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify


CACHE_TIME = 'long_term'


class CmsViews(object):

    def __init__(self, request):
        self.request = request
        self.repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')

    def get_repo_models(self):
        repo = pygit2.Repository(self.repo_path)
        ws = Workspace(repo.path, repo.head.name)
        return ws.import_models(cms_models)

    @reify
    def global_template(self):
        renderer = get_renderer("templates/base.pt")
        return renderer.implementation().macros['layout']

    @cache_region(CACHE_TIME)
    def get_categories(self):
        models = self.get_repo_models()
        return [c.to_dict() for c in models.Category().all()]

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        models = self.get_repo_models()
        return models.Category().get(uuid).to_dict()

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_id):
        models = self.get_repo_models()
        category = models.Category().get(category_id)
        return [
            p.to_dict()
            for p in models.Page().filter(primary_category=category)
        ]

    @cache_region(CACHE_TIME)
    def get_page(self, uuid):
        models = self.get_repo_models()
        return models.Page().get(uuid).to_dict()

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        return {'categories': self.get_categories()}

    @view_config(route_name='categories', renderer='templates/categories.pt')
    def categories(self):
        return {'categories': self.get_categories()}

    @view_config(route_name='category', renderer='cms:templates/category.pt')
    def category(self):
        category_id = self.request.matchdict['category']
        category = self.get_category(category_id)
        pages = self.get_pages_for_category(category_id)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='cms:templates/content.pt')
    def content(self):
        return {'page': self.get_page(self.request.matchdict['uuid'])}
