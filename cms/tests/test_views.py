import arrow
import json
import os
from datetime import timedelta, datetime
import pytz

from chameleon import PageTemplate
from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings
from pyramid.httpexceptions import HTTPNotFound

from cms import locale_negotiator_with_fallbacks
from cms.tests.base import UnicoreTestCase
from cms.views.cms_views import CmsViews

from unicore.content.models import Page, Category, Localisation


class TestViews(UnicoreTestCase):

    def setUp(self):
        self.workspace = self.mk_workspace()
        self.workspace.setup_custom_mapping(Page, {
            'properties': {
                'slug': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'language': {
                    'type': 'string',
                    'index': 'not_analyzed',
                }
            }
        })
        self.workspace.setup_custom_mapping(Category, {
            'properties': {
                'slug': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'language': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'position': {
                    'type': 'long'
                }
            }
        })

        self.workspace.setup_custom_mapping(Localisation, {
            'properties': {
                'locale': {
                    'type': 'string',
                    'index': 'not_analyzed',
                }
            }
        })

        languages = ("[('eng_GB', 'English'), ('swa_KE', 'Swahili'),"
                     "('spa_ES', 'Spanish'), ('fre_FR', 'French'),"
                     "('hin_IN', 'Hindi'), ('ind_ID', 'Bahasa'),"
                     "('per_IR', 'Persian'), ('grn_PY', 'Guarani')]")
        featured_langs = "[('spa_ES', 'Spanish'), ('eng_GB', 'English')]"

        settings = self.get_settings(
            self.workspace,
            available_languages=languages,
            featured_languages=featured_langs)

        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_chameleon')
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)
        self.views = CmsViews(self.mk_request())

        self.app = self.mk_app(self.workspace, settings=settings)

    def tearDown(self):
        testing.tearDown()

    def test_get_featured_pages(self):
        featured_pages = self.create_pages(
            self.workspace, count=2, featured=True)
        self.create_pages(self.workspace, count=2)
        self.assertEqual(
            set([p.uuid for p in featured_pages]),
            set([p.uuid for p in self.views.get_featured_pages(limit=10)]))

    def test_get_pages_count(self):
        self.create_pages(self.workspace, count=10)
        pages = self.views.get_pages(limit=7)
        self.assertEqual(len(pages), 7)

    def test_get_pages_order_by(self):
        self.create_pages(self.workspace, count=10)
        pages = self.views.get_pages(limit=2, order_by=('title',))
        self.assertEqual(
            [p.title for p in pages],
            ['Test Page 0', 'Test Page 1'])

    def test_get_pages_reversed(self):
        self.create_pages(
            self.workspace,
            count=10,
            timestamp_cb=lambda i: (
                arrow.utcnow() - timedelta(days=i)).isoformat())
        pages = self.views.get_pages(limit=2, order_by=('-modified_at',))
        self.assertEqual(
            [p.title for p in pages],
            ['Test Page 0', 'Test Page 1'])

    def test_get_available_languages(self):
        languages = self.views.get_available_languages
        self.assertEqual(languages[1][0], 'eng_GB')
        self.assertEqual(languages[7][0], 'swa_KE')
        self.assertEqual(languages[7][1], 'Kiswahili')

    def test_get_featured_category_pages(self):
        category1, category2 = self.create_categories(self.workspace)
        self.create_pages(
            self.workspace, count=10, primary_category=category1.uuid)
        featured_pages = self.create_pages(
            self.workspace, count=2, primary_category=category1.uuid,
            featured_in_category=True)

        page1, page2 = self.views.get_featured_category_pages(category1.uuid)
        self.assertEqual(
            set([page1.uuid, page2.uuid]),
            set([fp.uuid for fp in featured_pages]))

        self.assertEqual(
            set([page1.language, page2.language]),
            set(['eng_GB', 'eng_GB']))

        self.assertEqual(
            [], list(self.views.get_featured_category_pages(category2.uuid)))

    def test_get_featured_category_pages_swahili(self):
        self.views = CmsViews(self.mk_request(locale_name='swa_KE'))

        [category_eng] = self.create_categories(
            self.workspace, language='eng_GB', count=1)
        self.create_pages(
            self.workspace, count=10, language='eng_GB',
            primary_category=category_eng.uuid)
        self.create_pages(
            self.workspace, count=2, language='eng_GB',
            featured_in_category=True,
            primary_category=category_eng.uuid)

        [category_swh] = self.create_categories(
            self.workspace, language='swa_KE', count=1)
        self.create_pages(
            self.workspace, count=10, language='swa_KE',
            primary_category=category_swh.uuid)
        pages_swh_featured = self.create_pages(
            self.workspace, count=2, language='swa_KE',
            featured_in_category=True,
            primary_category=category_swh.uuid)

        # Assert english content not returned since language is swahili
        self.assertEqual(
            [],
            list(self.views.get_featured_category_pages(category_eng.uuid)))

        # Assert we get back featured pages for Swahili
        self.assertEqual(
            set([page.uuid for page in pages_swh_featured]),
            set([page.uuid
                 for page in
                 self.views.get_featured_category_pages(
                     category_swh.uuid)]))

    def test_get_page_by_slug(self):
        self.create_pages(self.workspace, count=5, language='eng_GB')
        self.create_pages(self.workspace, count=5, language='swa_KE')

        p = self.views.get_page(None, 'test-page-1', 'eng_GB')
        self.assertEqual(p.title, 'Test Page 1')
        self.assertEqual(p.language, 'eng_GB')

        p = self.views.get_page(None, 'test-page-1', 'swa_KE')
        self.assertEqual(p.language, 'swa_KE')
        self.assertEqual(self.views.get_page(None, 'invalid-slug'), None)

    def test_content_linked_pages(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page1] = self.create_pages(
            self.workspace,
            count=1, content='', description='',
            primary_category=category.uuid)
        [page2] = self.create_pages(
            self.workspace,
            count=1, content='', description='',
            linked_pages=[page1.uuid],
            primary_category=category.uuid)

        request = self.mk_request(matchdict={'uuid': page2.uuid})
        self.views = CmsViews(request)
        response = self.views.content()
        [linked_page] = response['linked_pages']
        self.assertEqual(linked_page, page1)

    def test_content_linked_pages_none(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page1] = self.create_pages(
            self.workspace,
            linked_pages=None,
            count=1, content='', description='',
            primary_category=category.uuid)
        request = self.mk_request(matchdict={'uuid': page1.uuid})
        self.views = CmsViews(request)
        response = self.views.content()
        self.assertEqual(list(response['linked_pages']), [])

    def test_content_markdown_rendering(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace,
            count=1,
            content='**strong**',
            description='_emphasised_',
            primary_category=category.uuid)

        request = self.mk_request(matchdict={'uuid': page.uuid})
        self.views = CmsViews(request)
        response = self.views.content()
        self.assertEqual(
            response['content'], '<p><strong>strong</strong></p>')
        self.assertEqual(
            response['description'], '<p><em>emphasised</em></p>')

    def test_views_no_primary_category(self):
        [page] = self.create_pages(
            self.workspace,
            linked_pages=None,
            count=1, content='', description='',
            primary_category=None)

        # checks that relevant views don't generate exceptions
        self.app.get('/')
        self.app.get('/spice/')
        self.app.get('/content/detail/%s/' % page.uuid)
        self.app.get('/spice/content/detail/%s/' % page.uuid)
        self.app.get('/content/comments/%s/' % page.uuid)

    def test_flatpage_markdown_rendering(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='**strong**',
            description='_emphasised_')

        request = self.mk_request(matchdict={'slug': page.slug})
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p><strong>strong</strong></p>')
        self.assertEqual(
            response['description'], '<p><em>emphasised</em></p>')

    def test_get_categories(self):
        category1, category2 = self.create_categories(
            self.workspace, language='eng_GB')
        category3, category4 = self.create_categories(
            self.workspace, language='swa_KE')

        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([category1.uuid, category2.uuid]),
            set([category.uuid
                 for category in self.views.get_categories()])
        )

        # Change language
        self.views = CmsViews(self.mk_request(locale_name='swa_KE'))
        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swa_KE', 'swa_KE']))

    def test_categories_ordering(self):
        category1 = Category(
            {'title': 'title 1', 'language': 'eng_GB', 'position': 3})
        category2 = Category(
            {'title': 'title 2', 'language': 'eng_GB', 'position': 0})
        category3 = Category(
            {'title': 'title 3', 'language': 'eng_GB', 'position': 1})
        category4 = Category(
            {'title': 'title 4', 'language': 'eng_GB', 'position': 2})
        self.workspace.save(category1, 'Update position')
        self.workspace.save(category2, 'Update position')
        self.workspace.save(category3, 'Update position')
        self.workspace.save(category4, 'Update position')
        self.workspace.refresh_index()

        cat1, cat2, cat3, cat4 = self.views.get_categories()

        self.assertEqual(cat1.uuid, category2.uuid)
        self.assertEqual(cat2.uuid, category3.uuid)
        self.assertEqual(cat3.uuid, category4.uuid)
        self.assertEqual(cat4.uuid, category1.uuid)

    def test_get_category(self):
        request = self.mk_request(locale_name='swa_KE')
        views = CmsViews(request)

        for does_not_exist in (None, 'abcd'):
            self.assertIs(views.get_category(does_not_exist), None)

    def test_pagination_first_page(self):
        [category] = self.create_categories(
            self.workspace, count=1, language='eng_GB')
        self.create_pages(self.workspace, count=15, content='baby',
                          primary_category=category.uuid)
        resp = self.app.get(
            '/content/list/%s/' % category.uuid,
            params={'p': '0'}, status=200)
        self.assertFalse('Previous' in resp.body)
        self.assertTrue('Next' in resp.body)

    def test_pagination_last_page(self):
        [category] = self.create_categories(
            self.workspace, count=1, language='eng_GB')
        self.create_pages(self.workspace, count=30, content='baby',
                          primary_category=category.uuid)
        resp = self.app.get(
            '/content/list/%s/' % category.uuid,
            params={'p': '3'}, status=200)
        self.assertTrue('Previous' in resp.body)
        self.assertFalse('Next' in resp.body)

    def test_pagination_middle_page(self):
        [category] = self.create_categories(
            self.workspace, count=1, language='eng_GB')
        self.create_pages(self.workspace, count=40, content='baby',
                          primary_category=category.uuid)
        resp = self.app.get(
            '/content/list/%s/' % category.uuid,
            params={'p': '2'}, status=200)
        self.assertTrue('Previous' in resp.body)
        self.assertTrue('Next' in resp.body)

    def test_pagination_results_per_page_configurable(self):
        settings = self.config.registry.settings.copy()
        settings["results_per_page"] = '5'
        app = self.mk_app(self.workspace, settings=settings)

        [category] = self.create_categories(
            self.workspace, count=1, language='eng_GB')
        self.create_pages(self.workspace, count=8, content='baby',
                          primary_category=category.uuid)
        resp = app.get(
            '/content/list/%s/' % category.uuid,
            params={'p': '0'}, status=200)
        self.assertTrue('Previous' not in resp.body)
        self.assertTrue('Next' in resp.body)

    def test_pagination_results_per_page_configurable_last_page(self):
        settings = self.config.registry.settings.copy()
        settings["results_per_page"] = '5'
        app = self.mk_app(self.workspace, settings=settings)

        [category] = self.create_categories(
            self.workspace, count=1, language='eng_GB')
        self.create_pages(self.workspace, count=8, content='baby',
                          primary_category=category.uuid)
        resp = app.get(
            '/content/list/%s/' % category.uuid,
            params={'p': '5'}, status=200)
        self.assertTrue('Previous' in resp.body)
        self.assertTrue('Next' not in resp.body)
        # check that we're on page 2
        self.assertTrue('<b>2</b>' in resp.body)

    def test_category_view(self):
        [category] = self.create_categories(
            self.workspace, count=1, language='swa_KE')
        [page] = self.create_pages(
            self.workspace, count=1, language='swa_KE',
            primary_category=category.uuid)

        request = self.mk_request(
            matchdict={'category': category.uuid}, locale_name='swa_KE')
        views = CmsViews(request)
        response = views.category()
        self.assertEqual(response['category'].uuid, category.uuid)
        self.assertEqual(
            [p.uuid for p in response['pages']], [page.uuid])

    def test_category_view_does_not_exist(self):
        request = self.mk_request(locale_name='swa_KE')
        views = CmsViews(request)

        for does_not_exist in (None, 'abcd'):
            request.matchdict['category'] = does_not_exist
            self.assertRaises(HTTPNotFound, views.category)

    def test_pages_ordering(self):
        [category] = self.create_categories(self.workspace, count=1)
        page1 = Page({
            'title': 'title 1', 'language': 'eng_GB', 'position': 3,
            'primary_category': category.uuid})
        page2 = Page({
            'title': 'title 2', 'language': 'eng_GB', 'position': 0,
            'primary_category': category.uuid})
        page3 = Page({
            'title': 'title 3', 'language': 'eng_GB', 'position': 1,
            'primary_category': category.uuid})
        page4 = Page({
            'title': 'title 4', 'language': 'eng_GB', 'position': 2,
            'primary_category': category.uuid})
        self.workspace.save(page1, 'Update position')
        self.workspace.save(page2, 'Update position')
        self.workspace.save(page3, 'Update position')
        self.workspace.save(page4, 'Update position')
        self.workspace.refresh_index()

        request = self.mk_request(matchdict={'category': category.uuid})
        views = CmsViews(request)
        cat = views.category()
        p1, p2, p3, p4 = cat['pages']

        self.assertEqual(p1.uuid, page2.uuid)
        self.assertEqual(p2.uuid, page3.uuid)
        self.assertEqual(p3.uuid, page4.uuid)
        self.assertEqual(p4.uuid, page1.uuid)

    def test_get_top_nav(self):
        category1, category2 = self.create_categories(self.workspace)
        category3, category4 = self.create_categories(
            self.workspace, language='swa_KE', featured_in_navbar=True)

        self.assertEqual([], list(self.views.get_top_nav))

        # Change language
        self.views = CmsViews(self.mk_request(locale_name='swa_KE'))
        cat1, cat2 = self.views.get_top_nav
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swa_KE', 'swa_KE']))

    def test_format_date_helper(self):
        views = CmsViews(self.mk_request())
        self.assertEqual(
            views.format_date('2014-10-10T09:10:17+00:00'),
            '10 October 2014')

        self.assertEqual(
            views.format_date('2014-10-10T09:10:17+00:00', '%d-%b-%y'),
            '10-Oct-14')

        self.assertEqual(
            views.format_date('some invalid date'),
            'some invalid date')

        dt = datetime(year=2014, month=10, day=10, hour=9, minute=10,
                      second=17, tzinfo=pytz.utc)
        self.assertEqual(
            views.format_date(dt), '10 October 2014')

    def test_get_flatpage_using_old_swahili_code(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='Sample page in swahili',
            description='_emphasised_', language='swa_KE')

        request = self.mk_request(
            {'_LOCALE_': 'swh_KE'}, matchdict={'slug': page.slug})
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p>Sample page in swahili</p>')

    def test_get_flatpage_using_old_english_code(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='Sample page in english',
            description='_emphasised_', language='eng_GB')

        request = self.mk_request(
            {'_LOCALE_': 'eng_UK'}, matchdict={'slug': page.slug})
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p>Sample page in english</p>')

    def test_image_url(self):
        self.views = CmsViews(self.mk_request())

        self.assertEqual(self.views.get_image_url(
            'http://some.site.com', 'sample-uuid-000000-0001'),
            'http://some.site.com/'
            '1bzRPrcuQPXBECF9mHxFVr11viY=/sample-uuid-000000-0001')

        self.assertEqual(self.views.get_image_url(
            'http://some.site.com', 'sample-uuid-000000-0001', 300, 200),
            'http://some.site.com/'
            '8Ko7ZiKCwOv8zDovqScWL5Lgrc8=/300x200/sample-uuid-000000-0001')

        self.assertEqual(self.views.get_image_url(
            'http://some.site.com', 'sample-uuid-000000-0001', 300),
            'http://some.site.com/'
            'LUyVe1umwB1caELC5m3LWu1HxvI=/300x0/sample-uuid-000000-0001')

        self.assertEqual(self.views.get_image_url(
            'http://some.site.com', 'sample-uuid-000000-0001', height=150),
            'http://some.site.com/'
            '4kS9gT_mYqVhnheDCuQhsahI_dU=/0x150/sample-uuid-000000-0001')

        self.assertEqual(self.views.get_image_url('', ''), '')

    def test_localisation(self):
        loc = Localisation({
            'locale': 'eng_GB',
            'image': 'sample-uuid-000000-0001',
            'image_host': 'http://some.site.com/'})
        self.workspace.save(loc, 'Add localisation')
        self.workspace.refresh_index()

        request = self.mk_request({'_LOCALE_': 'eng_GB'})
        self.views = CmsViews(request)

        localisation = self.views.get_localisation()
        self.assertEqual(localisation.locale, 'eng_GB')
        self.assertEqual(localisation.image, 'sample-uuid-000000-0001')
        self.assertEqual(localisation.image_host, 'http://some.site.com/')

        # Test fallbacks
        request = self.mk_request({'_LOCALE_': 'eng_UK'})
        self.views = CmsViews(request)

        localisation = self.views.get_localisation()
        self.assertEqual(localisation.locale, 'eng_GB')
        self.assertEqual(localisation.image, 'sample-uuid-000000-0001')
        self.assertEqual(localisation.image_host, 'http://some.site.com/')

    def test_localisation_not_found(self):
        loc = Localisation({
            'locale': 'eng_GB',
            'image': 'sample-uuid-000000-0001',
            'image_host': 'http://some.site.com/'})
        self.workspace.save(loc, 'Add localisation')
        self.workspace.refresh_index()

        request = self.mk_request({'_LOCALE_': 'spa_ES'})
        self.views = CmsViews(request)

        self.assertIsNone(self.views.get_localisation())

    def test_localised_logo(self):
        self.create_localisation(
            self.workspace,
            locale='eng_GB',
            logo_text='logo_text_foo',
            logo_description='logo_description_foo',
            logo_image='sample-uuid-000000-0002',
            logo_image_host='http://some.site.com/')

        def render_logo(locale, default_src=None):
            request = self.mk_request(locale_name=locale)
            self.views = CmsViews(request)
            if default_src:
                define = 'tal:define="img_attrs view.get_logo_attributes' \
                    '(default_image_src=\'%s\')"' % default_src
            else:
                define = ''
            template = '<div metal:use-macro="view.logo_template" %s></div>'
            template = PageTemplate(template % define)
            return template.render(view=self.views, request=request)

        localised_logo = render_logo('eng_GB')
        non_localised_logo = render_logo('spa_ES', '/default/logo.png')
        no_logo = render_logo('spa_ES')
        self.assertTrue('http://some.site.com/' in localised_logo)
        self.assertTrue('sample-uuid-000000-0002' in localised_logo)
        self.assertTrue('logo_description_foo' in localised_logo)
        self.assertFalse('logo-container' in no_logo)
        self.assertTrue('/default/logo.png' in non_localised_logo)

    def test_locale_cookie(self):
        [category1] = self.create_categories(
            self.workspace, count=1, locale='eng_GB', title='English Category')
        [category2] = self.create_categories(
            self.workspace, count=1, locale='spa_ES', title='Spanish Category')

        self.app.get('/locale/?language=eng_GB', status=302)
        resp = self.app.get('/', status=200)
        self.assertTrue('English Category' in resp.body)
        self.assertFalse('Spanish Category' in resp.body)

        self.app.get('/locale/?language=spa_ES', status=302)
        resp = self.app.get('/', status=200)
        self.assertTrue('Spanish Category' in resp.body)
        self.assertFalse('English Category' in resp.body)

        self.app.get('/locale/eng_GB/', status=302)
        resp = self.app.get('/', status=200)
        self.assertTrue('English Category' in resp.body)
        self.assertFalse('Spanish Category' in resp.body)

        self.app.get('/locale/spa_ES/', status=302)
        resp = self.app.get('/', status=200)
        self.assertTrue('Spanish Category' in resp.body)
        self.assertFalse('English Category' in resp.body)

    def test_locales_displayed(self):
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs, [('eng_GB', 'English'), ('spa_ES', u'espa\xf1ol')])

        request = self.mk_request(locale_name='fre_FR')
        self.views = CmsViews(request)
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs,
            [('fre_FR', u'fran\xe7ais'), ('eng_GB', 'English'),
             ('spa_ES', u'espa\xf1ol')])

        request = self.mk_request(locale_name='spa_ES')
        self.views = CmsViews(request)
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs, [('spa_ES', u'espa\xf1ol'), ('eng_GB', 'English')])

    def test_unsupported_locales(self):
        request = self.mk_request(locale_name='grn_PY')
        self.views = CmsViews(request)
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs,
            [('grn_PY', u'Guarani'), ('eng_GB', 'English'),
             ('spa_ES', u'espa\xf1ol')])

    def test_change_locale_page(self):
        resp = self.app.get('/locale/change/')
        self.assertTrue(
            u'<a href="/locale/spa_ES/">espa\xf1ol</a>'
            in resp.body.decode('utf-8'))
        self.assertTrue(
            u'<a href="/locale/eng_GB/">English</a>'
            in resp.body.decode('utf-8'))
        self.assertTrue(
            u'<a href="/locale/swa_KE/">Kiswahili</a>'
            in resp.body.decode('utf-8'))
        self.assertTrue(
            u'<a href="/locale/per_IR/">\u0641\u0627\u0631\u0633\u06cc</a>'
            in resp.body.decode('utf-8'))

    def test_404_page(self):
        resp = self.app.get('/;jsdafjahs;dfjas;', expect_errors=True)
        self.assertTrue('class="page-not-found"'in resp.body)
        self.assertEqual(resp.status_int, 404)

    def test_health(self):
        resp = self.app.get('/health/', status=200)
        data = json.loads(resp.body)
        self.assertEqual(data, {
            'version': None,
            'id': None,
        })

    def test_health_with_env_vars(self):
        os.environ['MARATHON_APP_ID'] = 'the-app-id'
        os.environ['MARATHON_APP_VERSION'] = 'the-app-version'
        resp = self.app.get('/health/', status=200)
        data = json.loads(resp.body)
        self.assertEqual(data, {
            'version': 'the-app-version',
            'id': 'the-app-id',
        })
        os.environ.pop('MARATHON_APP_ID')
        os.environ.pop('MARATHON_APP_VERSION')

    def test_repos(self):
        settings = self.config.registry.settings.copy()
        settings['es.index_prefix'] = 'foo'
        app = self.mk_app(self.workspace, settings=settings)

        resp = app.get('/repos.json', status=200)

        self.assertEqual(resp.json, [{
            'index': 'foo',
            'data': {'name': 'foo'}
        }])
