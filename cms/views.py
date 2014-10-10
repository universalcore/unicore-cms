from ast import literal_eval

from beaker.cache import cache_region

from gitmodel import exceptions

from markdown import markdown

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from cms.utils import CmsRepo

CACHE_TIME = 'default_term'


class CmsViews(object):

    def __init__(self, request):
        self.request = request
        self.repo_path = self.request.registry.settings['git.path']
        self.locale = request.locale_name
        self.repo = CmsRepo.read(self.repo_path)

    @reify
    def get_available_languages(self):
        langs = self.request.registry.settings.get(
            'available_languages', '[]')
        return literal_eval(langs)

    @reify
    def global_template(self):
        renderer = get_renderer("templates/base.pt")
        return renderer.implementation().macros['layout']

    def get_categories(self):
        return self._get_categories(self.locale)

    @cache_region(CACHE_TIME)
    def _get_categories(self, locale):
        models = self.repo.get_models()
        return models.GitCategoryModel().filter(language=locale)

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        models = self.repo.get_models()
        return models.GitCategoryModel().get(uuid)

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
        models = self.repo.get_models()
        sort_key = lambda page: [getattr(page, field) for field in order_by]
        latest_pages = sorted(
            models.GitPageModel().filter(language=self.locale),
            key=sort_key, reverse=reverse)[:limit]
        return latest_pages

    @cache_region(CACHE_TIME)
    def _get_featured_pages(self, locale, limit, order_by, reverse):
        models = self.repo.get_models()
        sort_key = lambda page: [getattr(page, field) for field in order_by]
        featured_pages = sorted(
            models.GitPageModel().filter(language=locale,
                                         featured=True),
            key=sort_key, reverse=reverse)[:limit]
        return featured_pages

    def get_featured_pages(self, limit=5, order_by=('modified_at',),
                           reverse=False):
        """
        Return featured pages the GitModel knows about.

        :param str locale:
            The locale string, like `eng_UK`.
        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on, defaults to ('modified_at',).
        :param bool reverse:
            Return the results in reverse order or not, defaults to False.
        """
        return self._get_featured_pages(self.locale, limit, order_by, reverse)

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_id, locale):
        models = self.repo.get_models()
        category = models.GitCategoryModel().get(category_id)
        return models.GitPageModel().filter(
            primary_category=category, language=locale)

    def get_featured_category_pages(self, category_id):
        return self._get_featured_category_pages(category_id, self.locale)

    @cache_region(CACHE_TIME)
    def _get_featured_category_pages(self, category_id, locale):
        models = self.repo.get_models()
        category = models.GitCategoryModel().get(category_id)
        return models.GitPageModel().filter(
            primary_category=category,
            featured_in_category=True,
            language=locale)

    @cache_region(CACHE_TIME)
    def get_page(self, uuid=None, slug=None, locale=None):
        models = self.repo.get_models()
        if uuid:
            return models.GitPageModel().get(uuid)
        if slug and locale:
            pages = models.GitPageModel().filter(slug=slug, language=locale)
            if any(pages):
                return pages[0]
        raise exceptions.DoesNotExist()

    @reify
    def get_top_nav(self):
        return self._get_top_nav(self.locale)

    @cache_region(CACHE_TIME)
    def _get_top_nav(self, locale):
        models = self.repo.get_models()
        return models.GitCategoryModel().filter(
            language=locale, featured_in_navbar=True)

    @view_config(route_name='home', renderer='templates/home.pt')
    @view_config(route_name='categories', renderer='templates/categories.pt')
    def categories(self):
        return {}

    @view_config(route_name='category', renderer='cms:templates/category.pt')
    def category(self):
        category_id = self.request.matchdict['category']
        category = self.get_category(category_id)

        if category.language != self.locale:
            raise HTTPNotFound()

        pages = self.get_pages_for_category(category_id, self.locale)
        return {'category': category, 'pages': pages}

    @view_config(route_name='content', renderer='cms:templates/content.pt')
    def content(self):
        page = self.get_page(self.request.matchdict['uuid'])
        if page.language != self.locale:
            raise HTTPNotFound()
        return {
            'page': page,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }

    @view_config(route_name='flatpage', renderer='cms:templates/flatpage.pt')
    def flatpage(self):
        try:
            page = self.get_page(
                None, self.request.matchdict['slug'], self.locale)

            if page.language != self.locale:
                raise exceptions.DoesNotExist()

            return {
                'page': page,
                'content': markdown(page.content),
                'description': markdown(page.description),
            }
        except exceptions.DoesNotExist:
            raise HTTPNotFound()

    @view_config(route_name='locale')
    def set_locale_cookie(self):
        if self.request.GET['language']:
            language = self.request.GET['language']
            response = Response()
            response.set_cookie('_LOCALE_',
                                value=language,
                                max_age=31536000)  # max_age = year
        return HTTPFound(location='/', headers=response.headers)
