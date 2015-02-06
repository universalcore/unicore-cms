from ast import literal_eval

from babel import Locale
from pycountry import languages

from beaker.cache import cache_region

from markdown import markdown

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from elasticgit import F

from cms.views.base import BaseCmsView

from unicore.content.models import Category, Page, Localisation
from utils import EGPaginator

from pyramid.view import notfound_view_config

CACHE_TIME = 'default_term'


class CmsViews(BaseCmsView):

    @reify
    def get_available_languages(self):
        available_languages = sorted(literal_eval(
            (self.settings.get('available_languages', '[]'))),
            key=lambda tup: tup[1].lower())
        return [
            (code, self.get_display_name(code))
            for code, name in available_languages]

    @reify
    def get_featured_languages(self):
        featured_languages = sorted(literal_eval(
            (self.settings.get('featured_languages', '[]'))),
            key=lambda tup: tup[1].lower())
        return [
            (code, self.get_display_name(code))
            for code, name in featured_languages]

    def get_display_name(self, locale):
        language_code, _, country_code = locale.partition('_')
        term_code = languages.get(bibliographic=language_code).terminology
        return Locale.parse(term_code).language_name

    def get_display_languages(self):
        to_display = [
            code for code, name in
            self.get_featured_languages or self.get_available_languages[:2]]

        featured_and_current = [self.locale] + sorted(list(
            set(to_display) - set([self.locale])),
            key=lambda tup: tup[1].lower())
        return [
            (code, self.get_display_name(code))
            for code in featured_and_current]

    @reify
    def global_template(self):
        renderer = get_renderer("cms:templates/base.pt")
        return renderer.implementation().macros['layout']

    @reify
    def paginator_template(self):
        renderer = get_renderer("cms:templates/paginator.pt")
        return renderer.implementation().macros['paginator']

    @reify
    def search_box_template(self):
        renderer = get_renderer("cms:templates/search_box.pt")
        return renderer.implementation().macros['search_box']

    def get_localisation(self):
        try:
            [localisation] = self.workspace.S(
                Localisation).filter(locale=self.locale)
            return localisation
        except ValueError:
            return None

    def get_categories(self, order_by=('position',)):
        return self._get_categories(self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_categories(self, locale, order_by):
        return self.workspace.S(Category).filter(
            language=locale).order_by(*order_by)

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        [category] = self.workspace.S(Category).filter(uuid=uuid)
        return category

    def get_pages(self, limit=5, order_by=('position', '-modified_at')):
        """
        Return pages the GitModel knows about.
        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on,
            defaults to ('position', '-modified_at')
        """
        return self.workspace.S(Page).filter(
            language=self.locale).order_by(*order_by)[:limit]

    @cache_region(CACHE_TIME)
    def _get_featured_pages(self, locale, limit, order_by):
        return self.workspace.S(Page).filter(
            language=locale, featured=True).order_by(*order_by)[:limit]

    def get_featured_pages(
            self, limit=5, order_by=('position', '-modified_at')):
        """
        Return featured pages the GitModel knows about.
        :param str locale:
            The locale string, like `eng_UK`.
        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on,
            defaults to ('position', '-modified_at').
        """
        return self._get_featured_pages(self.locale, limit, order_by)

    @cache_region(CACHE_TIME)
    def get_pages_for_category(
            self, category_id, locale, order_by=('position',)):
        return self.workspace.S(Page).filter(
            primary_category=category_id,
            language=locale).order_by(*order_by)

    def get_featured_category_pages(
            self, category_id, order_by=('position',)):
        return self._get_featured_category_pages(
            category_id, self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_featured_category_pages(self, category_id, locale, order_by):
        return self.workspace.S(Page).filter(
            primary_category=category_id, language=locale,
            featured_in_category=True).order_by(*order_by)

    @cache_region(CACHE_TIME)
    def get_page(self, uuid=None, slug=None, locale=None):
        try:
            query = self.workspace.S(Page).filter(
                F(uuid=uuid) | F(slug=slug))
            if locale is not None:
                query = query.filter(language=locale)
            [page] = query[:1]
            return page
        except ValueError:
            return None

    @reify
    def get_top_nav(self, order_by=('position',)):
        return self._get_top_nav(self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_top_nav(self, locale, order_by):
        return self.workspace.S(Category).filter(
            language=locale,
            featured_in_navbar=True).order_by(*order_by)

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

        if not page:
            raise HTTPNotFound()

        if page.linked_pages:
            linked_pages = self.workspace.S(Page).filter(
                uuid__in=page.linked_pages)
        else:
            linked_pages = []

        category = self.get_category(page.primary_category)
        if page.language != self.locale:
            raise HTTPNotFound()
        return {
            'page': page,
            'linked_pages': linked_pages,
            'primary_category': category,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }

    @view_config(route_name='flatpage', renderer='cms:templates/flatpage.pt')
    def flatpage(self):
        page = self.get_page(
            None, self.request.matchdict['slug'], self.locale)

        if not page:
            raise HTTPNotFound()

        if page.language != self.locale:
            raise HTTPNotFound()

        return {
            'page': page,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }

    @view_config(
        route_name='locale_change',
        renderer='cms:templates/locale_change.pt')
    def locale_change(self):
        return {
            'languages': self.get_featured_languages +
            sorted(list(set(self.get_available_languages) -
                        set(self.get_featured_languages)),
                   key=lambda tup: tup[1].lower())
        }

    @view_config(route_name='locale')
    @view_config(route_name='locale_matched')
    def set_locale_cookie(self):
        response = Response()
        language = self.request.matchdict.get('language') or \
            self.request.GET.get('language')

        if language:
            response.set_cookie('_LOCALE_', value=language, max_age=31536000)

        return HTTPFound(location='/', headers=response.headers)

    @view_config(route_name='search',
                 renderer='cms:templates/search_results.pt')
    def search(self):

        query = self.request.GET.get('q')
        p = int(self.request.GET.get('p', 0))

        empty_defaults = {
            'paginator': [],
            'query': query,
            'p': p,
        }

        # handle query exception
        if not query:
            return empty_defaults

        all_results = self.workspace.S(Page).query(content__query_string=query)

        # no results found
        if all_results.count() == 0:
            return empty_defaults

        paginator = EGPaginator(all_results, p)

        # requested page number is out of range
        total_pages = paginator.total_pages()
        # sets the floor to 0
        p = p if p >= 0 else 0
        # sets the roof to `total_pages -1`
        p = p if p < total_pages else total_pages - 1
        paginator = EGPaginator(all_results, p)

        return {
            'paginator': paginator,
            'query': query,
            'p': p,
        }

    @notfound_view_config(renderer='cms:templates/404.pt')
    def notfound(request):
        return {}
