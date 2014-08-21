import os
import pygit2
import shutil

from beaker.cache import cache_region
from cms import models as cms_models, utils
from gitmodel.workspace import Workspace

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound

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
    def get_category(self, slug):
        models = self.get_repo_models()
        return models.Category().get(slug).to_dict()

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_slug):
        models = self.get_repo_models()
        category = models.Category().get(category_slug)
        return [
            p.to_dict()
            for p in models.Page().filter(primary_category=category)
        ]

    @cache_region(CACHE_TIME)
    def get_page(self, id):
        models = self.get_repo_models()
        return models.Page().get(id).to_dict()

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        return {'categories': self.get_categories()}

    @view_config(route_name='categories', renderer='templates/categories.pt')
    def categories(self):
        return {'categories': self.get_categories()}

    @view_config(route_name='category', renderer='cms:templates/category.pt')
    def category(self):
        category_slug = self.request.matchdict['category']
        category = self.get_category(category_slug)
        pages = self.get_pages_for_category(category_slug)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='cms:templates/content.pt')
    def content(self):
        return {'page': self.get_page(self.request.matchdict['id'])}


class AdminViews(object):

    def __init__(self, request):
        self.request = request

    def get_ws(self):
        repo_path = self.request.registry.settings['git.path']
        repo = pygit2.Repository(repo_path)
        if repo.is_empty:
            return Workspace(repo.path)
        return Workspace(repo.path, repo.head.name)

    @view_config(route_name='configure', renderer='cms:templates/admin/configure.pt')
    def configure(self):
        repo_path = self.request.registry.settings['git.path']
        ws = self.get_ws()
        branches = utils.getall_branches(ws.repo)

        errors = []

        if self.request.method == 'POST':
            url = self.request.POST.get('url')
            if url:
                if ws.repo.is_empty:
                    shutil.rmtree(repo_path)
                    pygit2.clone_repository(url, repo_path)
                    self.get_ws().sync_repo_index()
            else:
                errors.append('Url is required')
        return {
            'repo': ws.repo,
            'errors': errors,
            'branches': [b.shorthand for b in branches],
            'current': ws.repo.head.shorthand if not ws.repo.is_empty else None
        }

    @view_config(route_name='configure_switch')
    def configure_switch(self):
        if self.request.method == 'POST':
            branch = self.request.POST.get('branch')
            if branch:
                self.get_ws().sync_repo_index()
                utils.checkout_branch(self.get_ws().repo, branch)
                self.get_ws().sync_repo_index()
        return HTTPFound(location=self.request.route_url('configure'))
