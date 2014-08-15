import os

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
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        ws = Workspace(repo_path)
        self.models = ws.import_models(cms_models)

    @reify
    def global_template(self):
        renderer = get_renderer("templates/base.pt")
        return renderer.implementation().macros['layout']

    @cache_region(CACHE_TIME)
    def get_categories(self):
        return [c.to_dict() for c in self.models.Category().all()]

    @cache_region(CACHE_TIME)
    def get_category(self, slug):
        return self.models.Category().get(slug).to_dict()

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_slug):
        category = self.models.Category().get(category_slug)
        return [
            p.to_dict()
            for p in self.models.Page().filter(primary_category=category)
        ]

    @cache_region(CACHE_TIME)
    def get_page(self, slug):
        return self.models.Page().get(slug).to_dict()

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        return {'categories': self.get_categories()}

    @view_config(route_name='category', renderer='templates/category.pt')
    def category(self):
        category_slug = self.request.matchdict['category']
        category = self.get_category(category_slug)
        pages = self.get_pages_for_category(category_slug)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='templates/content.pt')
    def content(self):
        return {'page': self.get_page(self.request.matchdict['slug'])}
