from ast import literal_eval

from beaker.cache import cache_region

from markdown import markdown

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from elasticgit import F

from cms.views.base import BaseCmsView

from unicore.content.models import Category, Page

CACHE_TIME = 'default_term'


class CmsViews(BaseCmsView):

    @reify
    def get_available_languages(self):
        return literal_eval(
            self.settings.get('available_languages', '[]'))

    @reify
    def global_template(self):
        renderer = get_renderer("cms:templates/base.pt")
        return renderer.implementation().macros['layout']

    def get_categories(self):
        return self._get_categories(self.locale)

    @cache_region(CACHE_TIME)
    def _get_categories(self, locale):
        return self.workspace.S(Category).filter(language=locale.lower())

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        [category] = self.workspace.S(Category).filter(uuid=uuid.lower())
        return category

    def get_pages(self, limit=5, order_by=('modified_at',)):
        """
        Return pages the GitModel knows about.

        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on, defaults to modified_at
        """
        return self.workspace.S(Page).filter(
            language=self.locale.lower()).order_by(*order_by)[:limit]

    @cache_region(CACHE_TIME)
    def _get_featured_pages(self, locale, limit, order_by):
        return self.workspace.S(Page).filter(
            language=locale.lower(), featured=True).order_by(*order_by)[:limit]

    def get_featured_pages(self, limit=5, order_by=('-modified_at',)):
        """
        Return featured pages the GitModel knows about.

        :param str locale:
            The locale string, like `eng_UK`.
        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on, defaults to ('modified_at',).
        """
        return self._get_featured_pages(self.locale, limit, order_by)

    @cache_region(CACHE_TIME)
    def get_pages_for_category(self, category_id, locale):
        return self.workspace.S(Page).filter(
            primary_category=category_id, language=locale.lower())

    def get_featured_category_pages(self, category_id):
        return self._get_featured_category_pages(category_id, self.locale)

    @cache_region(CACHE_TIME)
    def _get_featured_category_pages(self, category_id, locale):
        return self.workspace.S(Page).filter(
            primary_category=category_id, language=locale.lower(),
            featured_in_category=True)

    @cache_region(CACHE_TIME)
    def get_page(self, uuid=None, slug=None, locale=None):
        try:
            query = self.workspace.S(Page).filter(
                F(uuid=uuid) | F(slug=slug))
            if locale is not None:
                query = query.filter(language=locale.lower())
            [page] = query[:1]
            return page
        except ValueError:
            raise HTTPNotFound()

    @reify
    def get_top_nav(self):
        return self._get_top_nav(self.locale)

    @cache_region(CACHE_TIME)
    def _get_top_nav(self, locale):
        return self.workspace.S(Category).filter(
            language=locale.lower(), featured_in_navbar=True)

    @view_config(route_name='home', renderer='cms:templates/home.pt')
    @view_config(route_name='categories',
                 renderer='cms:templates/categories.pt')
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
        category = self.get_category(page.primary_category)
        if page.language != self.locale:
            raise HTTPNotFound()
        return {
            'page': page,
            'primary_category': category,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }

    @view_config(route_name='flatpage', renderer='cms:templates/flatpage.pt')
    def flatpage(self):
        page = self.get_page(
            None, self.request.matchdict['slug'], self.locale)

        if page.language != self.locale:
            raise HTTPNotFound()

        return {
            'page': page,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }

    @view_config(route_name='locale')
    def set_locale_cookie(self):
        if self.request.GET['language']:
            language = self.request.GET['language']
            response = Response()
            response.set_cookie('_LOCALE_',
                                value=language,
                                max_age=31536000)  # max_age = year
        return HTTPFound(location='/', headers=response.headers)
