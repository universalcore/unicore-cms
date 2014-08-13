import os
from gitmodel.workspace import Workspace
from pyramid.view import view_config
from cms import models as cms_models

from pyramid.renderers import get_renderer
from pyramid.decorator import reify


class CmsViews(object):
    def __init__(self, request):
        self.request = request

    @reify
    def global_template(self):
        renderer = get_renderer("templates/base.pt")
        return renderer.implementation().macros['layout']

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        ws = Workspace(repo_path)
        models = ws.import_models(cms_models)
        categories = models.Category().all()
        return {'categories': categories}

    @view_config(route_name='category', renderer='templates/category.pt')
    def category(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        ws = Workspace(repo_path)
        models = ws.import_models(cms_models)
        category = models.Category().get(self.request.matchdict['category'])
        pages = models.Page().filter(primary_category=category)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='templates/content.pt')
    def content(self):
        repo_path = os.path.join(
            self.request.registry.settings['git.path'], '.git')
        ws = Workspace(repo_path)
        models = ws.import_models(cms_models)
        page = models.Page().get(self.request.matchdict['slug'])
        return {'page': page}
