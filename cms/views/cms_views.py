from ast import literal_eval
from datetime import datetime
from os import environ
import pytz

from babel import Locale, UnknownLocaleError
from pycountry import languages

from beaker.cache import cache_region

from markdown import markdown
import colander
from deform import ValidationFailure

from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.decorator import reify
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPBadRequest

from elasticgit import F

from cms import USER_DATA_SESSION_KEY
from cms.views.base import BaseCmsView
from cms.views.utils import (
    EGPaginator, to_eg_objects, translation_string_factory as _, ga_context)
from cms.views.forms import CommentForm
from cms.tasks import pull

from unicore.content.models import Category, Page, Localisation
from unicore.hub.client import ClientException as HubClientException
from unicore.hub.client.utils import same_origin
from unicore.comments.client import (
    LazyCommentPage, UserBanned, CommentStreamNotOpen, CommentServiceException)

from pyramid.view import notfound_view_config

CACHE_TIME = 'default_term'
COMMENTS_PER_PAGE = 20


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

        available_languages = dict(literal_eval(
            (self.settings.get('available_languages', '[]'))))

        try:
            return Locale.parse(term_code).language_name
        except UnknownLocaleError:
            # Fallback value is the generated value in English or the code
            return available_languages.get(locale, locale)

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
    def paginator_template_category(self):
        renderer = get_renderer("cms:templates/paginator_category.pt")
        return renderer.implementation().macros['paginator']

    @reify
    def paginator_template(self):
        renderer = get_renderer("cms:templates/paginator.pt")
        return renderer.implementation().macros['paginator']

    @reify
    def search_box_template(self):
        renderer = get_renderer("cms:templates/search_box.pt")
        return renderer.implementation().macros['search_box']

    @reify
    def logo_template(self):
        renderer = get_renderer("cms:templates/logo.pt")
        return renderer.implementation().macros['logo']

    @reify
    def auth_template(self):
        renderer = get_renderer("cms:templates/auth.pt")
        return renderer.implementation().macros['auth']

    def get_logo_attributes(self, default_image_src=None,
                            width=None, height=None):
        attrs = {'width': width, 'height': height}
        localisation = self.get_localisation()

        if not localisation:
            attrs.update({'src': default_image_src, 'alt': None})
            return attrs

        attrs['alt'] = localisation.logo_description or None
        if localisation.logo_image:
            attrs['src'] = self.get_image_url(localisation.logo_image_host,
                                              localisation.logo_image)
        else:
            attrs['src'] = default_image_src
        return attrs

    def get_localisation(self):
        try:
            [localisation] = self.workspace.S(
                Localisation).filter(locale=self.locale)
            return localisation.to_object()
        except ValueError:
            return None

    def get_categories(self, order_by=('position',)):
        return self._get_categories(self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_categories(self, locale, order_by):
        return to_eg_objects(self.workspace.S(Category).filter(
            language=locale).order_by(*order_by))

    @cache_region(CACHE_TIME)
    def get_category(self, uuid):
        try:
            [category] = self.workspace.S(Category).filter(uuid=uuid)
            return category.to_object()
        except ValueError:
            return None

    def get_pages(self, limit=5, order_by=('position', '-modified_at')):
        """
        Return pages the GitModel knows about.
        :param int limit:
            The number of pages to return, defaults to 5.
        :param tuple order_by:
            The attributes to order on,
            defaults to ('position', '-modified_at')
        """
        return to_eg_objects(self.workspace.S(Page).filter(
            language=self.locale).order_by(*order_by)[:limit])

    @cache_region(CACHE_TIME)
    def _get_featured_pages(self, locale, limit, order_by):
        return to_eg_objects(self.workspace.S(Page).filter(
            language=locale, featured=True).order_by(*order_by)[:limit])

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
        return self.workspace.S(Page)[:10000].filter(
            primary_category=category_id,
            language=locale).order_by(*order_by)

    def get_featured_category_pages(
            self, category_id, order_by=('position',)):
        return self._get_featured_category_pages(
            category_id, self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_featured_category_pages(self, category_id, locale, order_by):
        return to_eg_objects(self.workspace.S(Page).filter(
            primary_category=category_id, language=locale,
            featured_in_category=True).order_by(*order_by))

    @cache_region(CACHE_TIME)
    def get_page(self, uuid=None, slug=None, locale=None):
        try:
            query = self.workspace.S(Page).filter(
                F(uuid=uuid) | F(slug=slug))
            if locale is not None:
                query = query.filter(language=locale)
            [page] = query[:1]
            return page.to_object()
        except ValueError:
            return None

    def get_comments_for_content(self, content_uuid, **page_args):
        commentclient = self.request.registry.commentclient
        if commentclient is None:
            return None

        default_page_args = {'limit': COMMENTS_PER_PAGE}

        if 'c_after' in self.request.GET:
            default_page_args['after'] = self.request.GET['c_after']
        elif 'c_before' in self.request.GET:
            default_page_args['before'] = self.request.GET['c_before']

        default_page_args.update(page_args)

        return LazyCommentPage(
            commentclient,
            content_uuid=content_uuid,
            app_uuid=commentclient.settings['app_id'],
            **default_page_args)

    def get_comment_context(self, content_object):
        return {
            'comments': self.get_comments_for_content(
                content_object.uuid, limit=COMMENTS_PER_PAGE),
            'comment_form': CommentForm(self.request, content_object)
        }

    @reify
    def get_top_nav(self, order_by=('position',)):
        return self._get_top_nav(self.locale, order_by)

    @cache_region(CACHE_TIME)
    def _get_top_nav(self, locale, order_by):
        return to_eg_objects(self.workspace.S(Category).filter(
            language=locale,
            featured_in_navbar=True).order_by(*order_by))

    @view_config(route_name='health', renderer='json')
    def health(self):
        app_id = environ.get('MARATHON_APP_ID', None)
        ver = environ.get('MARATHON_APP_VERSION', None)
        return {'id': app_id, 'version': ver}

    @ga_context(lambda context: {'dt': 'Home', })
    @view_config(route_name='home', renderer='cms:templates/home.pt')
    @view_config(route_name='home_jinja', renderer='cms:templates/home.jinja2')
    # redundantcategory
    @view_config(route_name='categories',
                 renderer='cms:templates/categories.pt')
    def categories(self):
        return {}

    @ga_context(lambda context: {'dt': context['category'].title, })
    @view_config(route_name='category', renderer='cms:templates/category.pt')
    @view_config(route_name='category_jinja2',
                 renderer='cms:templates/category.jinja2')
    def category(self):
        category_id = self.request.matchdict['category']
        category = self.get_category(category_id)

        if category is None or category.language != self.locale:
            raise HTTPNotFound()

        pages = self.get_pages_for_category(category_id, self.locale)
        p = int(self.request.GET.get('p', 0))
        empty_defaults = {
            'paginator': [],
            'category': category,
            'p': p,
        }
        if not category:
            return empty_defaults

        if len(pages) == 0:
            return empty_defaults
        paginator = EGPaginator(
            pages, p, results_per_page=self.results_per_page)

        # requested page number is out of range
        total_pages = paginator.total_pages()
        # sets the floor to 0
        p = p if p >= 0 else 0
        # sets the roof to `total_pages -1`
        p = p if p < total_pages else total_pages - 1
        paginator = EGPaginator(
            pages, p, results_per_page=self.results_per_page)

        return {
            'paginator': paginator,
            'category': category,
            'p': p,
            'pages': pages,
        }

    @ga_context(lambda context: {'dt': context['page'].title, })
    @view_config(route_name='content', renderer='cms:templates/content.pt')
    @view_config(route_name='content_jinja',
                 renderer='cms:templates/content.jinja2')
    def content(self):
        page = self.get_page(self.request.matchdict['uuid'])

        if not page:
            raise HTTPNotFound()

        if page.linked_pages:
            linked_pages = to_eg_objects(self.workspace.S(Page).filter(
                uuid__in=page.linked_pages))
        else:
            linked_pages = []

        category = None
        if page.primary_category:
            category = self.get_category(page.primary_category)

        if page.language != self.locale:
            raise HTTPNotFound()

        context = {
            'page': page,
            'linked_pages': linked_pages,
            'primary_category': category,
            'content': markdown(page.content),
            'description': markdown(page.description),
        }
        context.update(self.get_comment_context(page))
        return context

    @view_config(route_name='comments',
                 renderer='cms:templates/comments/comment_page.jinja2')
    def comments(self):
        context = self.content()

        if 'submit' in self.request.POST:
            form = context['comment_form']

            try:
                data = form.validate(self.request.POST.items())
                commentclient = self.request.registry.commentclient
                commentclient.create_comment(data)
                raise HTTPFound(self.request.route_url(
                    'comments', uuid=data['content_uuid']))

            except ValidationFailure as e:
                context['comment_form'] = e.field

            except UserBanned:
                form.error = colander.Invalid(
                    form, _('You have been banned from commenting'))

            except CommentStreamNotOpen:
                raise HTTPFound(self.request.route_url(
                    'comments', uuid=data['content_uuid']))

            except ValueError as e:
                raise HTTPBadRequest()

        return context

    @view_config(route_name='flag_comment')
    def flag_comment(self):
        commentclient = self.request.registry.commentclient

        if None in (self.request.user, commentclient):
            raise HTTPNotFound

        flag_data = {
            'user_uuid': self.request.user.get('uuid'),
            'comment_uuid': self.request.matchdict['uuid'],
            'submit_datetime': datetime.now(pytz.utc).isoformat(),
            'app_uuid': commentclient.settings['app_id']
        }
        try:
            commentclient.create_flag(flag_data)
        except CommentServiceException as e:
            if e.response.status_code == 404:
                raise HTTPNotFound
            raise e

        query = {}
        if self.request.referrer and same_origin(
                self.request.referrer, self.request.current_route_url()):
            query = {'next': self.request.referrer}

        return HTTPFound(self.request.route_url(
            'flag_comment_success', uuid=flag_data['comment_uuid'],
            _query=query))

    @view_config(route_name='flag_comment_success',
                 renderer='cms:templates/comments/comment_flagged.jinja2')
    def flag_comment_success(self):
        if not self.request.user:
            raise HTTPNotFound

        next_url = self.request.GET.get('next')
        if next_url and not same_origin(
                next_url, self.request.current_route_url()):
            next_url = None

        return {'next': next_url}

    @ga_context(lambda context: {'dt': context['page'].title, })
    @view_config(route_name='flatpage', renderer='cms:templates/flatpage.pt')
    @view_config(route_name='flatpage_jinja',
                 renderer='cms:templates/flatpage.jinja2')
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

    @ga_context(lambda context: {'dt': 'Choose Language', })
    @view_config(
        route_name='locale_change',
        renderer='cms:templates/locale_change.pt')
    @view_config(
        route_name='locale_change_jinja',
        renderer='cms:templates/locale_change.jinja2')
    def locale_change(self):
        return {
            'languages': self.get_featured_languages +
            sorted(list(set(self.get_available_languages) -
                        set(self.get_featured_languages)),
                   key=lambda tup: tup[1].lower())
        }

    @ga_context(lambda context: {'dt': 'Set Language', })
    @view_config(route_name='locale')
    @view_config(route_name='locale_matched')
    def set_locale_cookie(self):
        response = Response()
        language = self.request.matchdict.get('language') or \
            self.request.GET.get('language')

        if language:
            response.set_cookie('_LOCALE_', value=language, max_age=31536000)

        return HTTPFound(location='/', headers=response.headers)

    @ga_context(lambda context: {'dt': 'Search', })
    @view_config(route_name='search',
                 renderer='cms:templates/search_results.pt')
    @view_config(route_name='search_jinja',
                 renderer='cms:templates/search_results.jinja2')
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

        all_results = self.workspace.S(Page).query(
            content__query_string=query).filter(language=self.locale)

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
    def notfound(self):
        self.request.response.status = 404
        return {}

    @view_config(route_name='login')
    def login(self):
        hubclient = self.request.registry.hubclient
        response = HTTPFound()

        # redeem ticket to get user data
        ticket = self.request.GET.get('ticket', None)
        if ticket and hubclient:
            try:
                user = hubclient.get_user(
                    ticket, self.request.route_url('redirect_to_login'))
                self.request.session[USER_DATA_SESSION_KEY] = user.data
                user_id = user.get('uuid')
                headers = remember(self.request, user_id)
                response.headerlist.extend(headers)

            except HubClientException:
                # TODO: what to do when ticket is invalid?
                pass

        redirect_url = self.request.GET.get('url', None)
        if not (redirect_url and same_origin(
                redirect_url, self.request.current_route_url())):
            redirect_url = self.request.route_url(route_name='home')
        response.location = redirect_url

        return response

    @view_config(route_name='redirect_to_login')
    def redirect_to_login(self):
        hubclient = self.request.registry.hubclient

        if self.request.referrer and same_origin(
                self.request.referrer, self.request.current_route_url()):
            callback_url = self.request.route_url(
                route_name='login', _query={'url': self.request.referrer})
        else:
            callback_url = self.request.route_url(route_name='login')

        if hubclient is None:
            # benign redirect if hubclient is not configured
            return HTTPFound(callback_url)

        return HTTPFound(hubclient.get_login_redirect_url(
            callback_url, locale=self.locale))

    @view_config(route_name='logout')
    def logout(self):
        response = HTTPFound(headers=forget(self.request))

        if self.request.referrer and same_origin(
                self.request.referrer, self.request.current_route_url()):
            response.location = self.request.referrer
        else:
            response.location = self.request.route_url(route_name='home')

        return response

    @view_config(route_name='api_notify', renderer='json')
    def api_notify(self):
        pull.delay(
            self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'],
            es=self.es_settings)
        return {}

    @view_config(route_name='repos', renderer='json')
    def repos(self):
        index = self.settings['es.index_prefix']

        return [{
            'index': index,
            'data': {'name': index},
        }]
