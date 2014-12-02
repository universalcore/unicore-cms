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

    @view_config(route_name='locale')
    def set_locale_cookie(self):
        if self.request.GET['language']:
            language = self.request.GET['language']
            response = Response()
            response.set_cookie('_LOCALE_',
                                value=language,
                                max_age=31536000)  # max_age = year
        return HTTPFound(location='/', headers=response.headers)

    @view_config(route_name='search', renderer='cms:templates/search.pt')
    def search(self):
        results_per_page = 10
        query = self.request.GET.get('q')
        p = self.request.GET.get('p')

        # handle query exception
        if not query:
            return {'results': [],
                    'query': query,
                    'p': None,
                    'page_numbers': None,
                    'total_pages': None,
                    'total': None,
                    'previous_page': None,
                    'next_page': None}

        # case where search is typed directly into searchbar
        if p is None:
            p = 1
        else:
            p = int(self.request.GET.get('p'))

        all_results = self.workspace.S(Page).query(content__query_string=query)

        # get the total number of results
        total = all_results.count()

        # no results found
        if total == 0:
            return {'results': [],
                    'query': query,
                    'p': None,
                    'page_numbers': None,
                    'total_pages': None,
                    'total': None,
                    'previous_page': None,
                    'next_page': None}

        # get the total number of pages
        remainder = total % results_per_page
        if(remainder == 0):
            total_pages = total / results_per_page
        else:
            total_pages = (
                (total + (results_per_page - (remainder))) / results_per_page)

        # create sliding range of page numbers
        # slider value should be odd and never less than 3
        slider_value = 5
        buffer_value = slider_value / 2

        page_numbers = []
        # get buffered values either side of the current page number
        if (p - buffer_value <= 1):
            count = 1
            while((count <= slider_value)and(count <= total_pages)):
                page_numbers.append(count)
                count += 1

        elif (p + buffer_value >= total_pages):
            count = total_pages
            while((count >= total_pages - slider_value)and(count >= 1)):
                page_numbers.insert(0, count)
                count -= 1

        else:
            count = -buffer_value
            while (count <= buffer_value):
                buffer_page = p + count
                if(buffer_page >= 1) and (buffer_page <= total_pages):
                    page_numbers.append(p + count)
                count += 1

        # determine if first-page-number-link should be displayed
        need_start = True
        if page_numbers[0] == 1:
            need_start = False

        # determine if start ellipsis are needed
        need_start_ellipsis = True
        if page_numbers[0] <= 2:
            need_start_ellipsis = False

        # determine if end ellipsis are needed
        need_end_ellipsis = True
        if (page_numbers[-1]) >= (total_pages - 1):
            need_end_ellipsis = False

        # determine if last-page-number-link should be displayed
        need_end = True
        if page_numbers[-1] == total_pages:
            need_end = False

        # get specified number of results
        results = all_results.order_by(
            '_score')[(p * results_per_page - results_per_page):
                      p * results_per_page]

        # determine whether there there is a previous page
        if (p * results_per_page) > results_per_page:
            previous_page = p - 1
        else:
            previous_page = None

        # determine whether there is a next page
        if (p + 1 <= total_pages):
            next_page = p + 1
        else:
            next_page = None

        return {'results': results,
                'query': query,
                'p': p,
                'need_start': need_start,
                'need_start_ellipsis': need_start_ellipsis,
                'page_numbers': page_numbers,
                'need_end_ellipsis': need_end_ellipsis,
                'need_end': need_end,
                'total_pages': total_pages,
                'total': total,
                'previous_page': previous_page,
                'next_page': next_page}
