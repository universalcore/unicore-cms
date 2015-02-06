import arrow
from datetime import timedelta

from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings


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
                     "('per_IR', 'Persian')]")
        featured_langs = "[('spa_ES', 'Spanish'), ('eng_GB', 'English')]"

        settings = {
            'git.path': self.workspace.repo.working_dir,
            'git.content_repo_url': '',
            'es.index_prefix': self.workspace.index_prefix,
            'cache.enabled': 'false',
            'cache.regions': 'long_term, default_term',
            'cache.long_term.expire': '1',
            'cache.default_term.expire': '1',
            'available_languages': languages,
            'featured_languages': featured_langs,
            'pyramid.default_locale_name': 'eng_GB',
            'thumbor.security_key': 'sample-security-key',
            'thumbor.server': 'http://some.site.com',
        }

        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)
        self.views = CmsViews(testing.DummyRequest())

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
        self.assertEqual(languages[6][0], 'swa_KE')
        self.assertEqual(languages[6][1], 'Kiswahili')

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
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swa_KE'}))

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

        request = testing.DummyRequest()
        request.matchdict['uuid'] = page2.uuid
        self.views = CmsViews(request)
        response = self.views.content()
        [linked_page] = response['linked_pages']
        self.assertEqual(linked_page.get_object(), page1)

    def test_content_linked_pages_none(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page1] = self.create_pages(
            self.workspace,
            linked_pages=None,
            count=1, content='', description='',
            primary_category=category.uuid)
        request = testing.DummyRequest()
        request.matchdict['uuid'] = page1.uuid
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

        request = testing.DummyRequest()
        request.matchdict['uuid'] = page.uuid
        self.views = CmsViews(request)
        response = self.views.content()
        self.assertEqual(
            response['content'], '<p><strong>strong</strong></p>')
        self.assertEqual(
            response['description'], '<p><em>emphasised</em></p>')

    def test_flatpage_markdown_rendering(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='**strong**',
            description='_emphasised_')

        request = testing.DummyRequest()
        request.matchdict['slug'] = page.slug
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
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swa_KE'}))
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
        [category] = self.create_categories(
            self.workspace, count=1, language='swa_KE')
        [page] = self.create_pages(
            self.workspace, count=1, language='swa_KE',
            primary_category=category.uuid)

        request = testing.DummyRequest({'_LOCALE_': 'swa_KE'})
        request.matchdict['category'] = category.uuid
        views = CmsViews(request)
        response = views.category()
        self.assertEqual(response['category'].uuid, category.uuid)
        self.assertEqual(
            [p.uuid for p in response['pages']], [page.uuid])

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

        request = testing.DummyRequest({})
        request.matchdict['category'] = category.uuid
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
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swa_KE'}))
        cat1, cat2 = self.views.get_top_nav
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swa_KE', 'swa_KE']))

    def test_format_date_helper(self):
        views = CmsViews(testing.DummyRequest({}))
        self.assertEqual(
            views.format_date('2014-10-10T09:10:17+00:00'),
            '10 October 2014')

        self.assertEqual(
            views.format_date('2014-10-10T09:10:17+00:00', '%d-%b-%y'),
            '10-Oct-14')

        self.assertEqual(
            views.format_date('some invalid date'),
            'some invalid date')

    def test_get_flatpage_using_old_swahili_code(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='Sample page in swahili',
            description='_emphasised_', language='swa_KE')

        request = testing.DummyRequest({'_LOCALE_': 'swh_KE'})
        request.matchdict['slug'] = page.slug
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p>Sample page in swahili</p>')

    def test_get_flatpage_using_old_english_code(self):
        [category] = self.create_categories(self.workspace, count=1)
        [page] = self.create_pages(
            self.workspace, count=1, content='Sample page in english',
            description='_emphasised_', language='eng_GB')

        request = testing.DummyRequest({'_LOCALE_': 'eng_UK'})
        request.matchdict['slug'] = page.slug
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p>Sample page in english</p>')

    def test_image_url(self):
        self.views = CmsViews(testing.DummyRequest({}))

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

        request = testing.DummyRequest({'_LOCALE_': 'eng_GB'})
        self.views = CmsViews(request)

        localisation = self.views.get_localisation()
        self.assertEqual(localisation.locale, 'eng_GB')
        self.assertEqual(localisation.image, 'sample-uuid-000000-0001')
        self.assertEqual(localisation.image_host, 'http://some.site.com/')

        # Test fallbacks
        request = testing.DummyRequest({'_LOCALE_': 'eng_UK'})
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

        request = testing.DummyRequest({'_LOCALE_': 'spa_ES'})
        self.views = CmsViews(request)

        self.assertIsNone(self.views.get_localisation())

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

        request = testing.DummyRequest({'_LOCALE_': 'fre_FR'})
        self.views = CmsViews(request)
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs,
            [('fre_FR', u'fran\xe7ais'), ('eng_GB', 'English'),
             ('spa_ES', u'espa\xf1ol')])

        request = testing.DummyRequest({'_LOCALE_': 'spa_ES'})
        self.views = CmsViews(request)
        langs = self.views.get_display_languages()
        self.assertEqual(
            langs, [('spa_ES', u'espa\xf1ol'), ('eng_GB', 'English')])

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
        resp = self.app.get('/;jsdafjahs;dfjas;')
        self.assertTrue('class="page-not-found"'in resp.body)
