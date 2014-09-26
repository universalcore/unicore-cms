import pygit2

from beaker.cache import cache_region

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify

from unicore_gitmodels import models
from cms import utils

CACHE_TIME = 'long_term'


class CmsViews(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.repo_path = self.request.registry.settings['git.path']

    def get_repo_models(self):
        repo = pygit2.Repository(self.repo_path)
        ws = utils.get_workspace(repo)
        return ws.import_models(models)

    @reify
    def global_template(self):
        renderer = get_renderer("templates/base.pt")
        return renderer.implementation().macros['layout']

    @cache_region(CACHE_TIME)
    def get_categories(self):
        models = self.get_repo_models()
        return [c.to_dict() for c in models.GitCategoryModel().all()]

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        models = self.get_repo_models()
        return models.GitCategoryModel().get(uuid).to_dict()

    def get_pages(self, limit=5, order_by=('modified_at',), reverse=False):
        """
        Return pages the GitModel knows about.

        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on, defaults to modified_at
        :param bool reverse:
            Return the results in reverse order or not, defaults to False
        """
        models = self.get_repo_models()
        sort_key = lambda page: [getattr(page, field) for field in order_by]
        latest_pages = sorted(models.GitPageModel().all(),
                              key=sort_key, reverse=reverse)[:limit]
        return [c.to_dict() for c in latest_pages]

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_id):
        models = self.get_repo_models()
        category = models.GitCategoryModel().get(category_id)
        return [
            p.to_dict()
            for p in models.GitPageModel().filter(primary_category=category)
        ]

    # @cache_region(CACHE_TIME)
    def get_featured_category_pages(self, category_id):
        models = self.get_repo_models()
        category = models.GitCategoryModel().get(category_id)
        return [
            p.to_dict()
            for p in models.GitPageModel().filter(
                primary_category=category,
                featured_in_category=True)
        ]

    @cache_region(CACHE_TIME)
    def get_page(self, uuid):
        models = self.get_repo_models()
        return models.GitPageModel().get(uuid).to_dict()

    @reify
    def get_top_nav(self):
        return self.get_categories()

    @view_config(route_name='home', renderer='templates/home.pt')
    @view_config(route_name='categories', renderer='templates/categories.pt')
    def categories(self):
        return {}

    @view_config(route_name='category', renderer='cms:templates/category.pt')
    def category(self):
        category_id = self.request.matchdict['category']
        category = self.get_category(category_id)
        pages = self.get_pages_for_category(category_id)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='cms:templates/content.pt')
    def content(self):
        return {'page': self.get_page(self.request.matchdict['uuid'])}
