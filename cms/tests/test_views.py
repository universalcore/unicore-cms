import arrow
from datetime import timedelta

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid_beaker import set_cache_regions_from_settings

from cms.tests.base import UnicoreTestCase
from cms.views.cms_views import CmsViews

from unicore.content.models import Page


class TestViews(UnicoreTestCase):

    def setUp(self):
        self.workspace = self.mk_workspace()
        languages = "[('eng_UK', 'English'), ('swh_KE', 'Swahili (Kenya)')]"
        settings = {
            'git.path': self.workspace.repo.working_dir,
            'git.content_repo_url': '',
            'es.index_prefix': self.workspace.index_prefix,
            'cache.enabled': 'false',
            'cache.regions': 'long_term, default_term',
            'cache.long_term.expire': '1',
            'cache.default_term.expire': '1',
            'available_languages': languages,
            'pyramid.default_locale_name': 'eng_UK',
        }
        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.views = CmsViews(testing.DummyRequest())

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
        self.assertEqual(languages[0][0], 'eng_UK')
        self.assertEqual(languages[1][0], 'swh_KE')
        self.assertEqual(languages[1][1], 'Swahili (Kenya)')

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
            set(['eng_UK', 'eng_UK']))

        self.assertEqual(
            [], list(self.views.get_featured_category_pages(category2.uuid)))

    def test_get_featured_category_pages_swahili(self):
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))

        [category_eng] = self.create_categories(
            self.workspace, language='eng_UK', count=1)
        self.create_pages(
            self.workspace, count=10, language='eng_UK',
            primary_category=category_eng.uuid)
        self.create_pages(
            self.workspace, count=2, language='eng_UK',
            featured_in_category=True,
            primary_category=category_eng.uuid)

        [category_swh] = self.create_categories(
            self.workspace, language='swh_KE', count=1)
        self.create_pages(
            self.workspace, count=10, language='swh_KE',
            primary_category=category_swh.uuid)
        pages_swh_featured = self.create_pages(
            self.workspace, count=2, language='swh_KE',
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
        self.workspace.setup_custom_mapping(Page, {
            'properties': {
                'slug': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'language': {
                    'type': 'string',
                }
            }
        })

        self.create_pages(self.workspace, count=5, language='eng_UK')
        self.create_pages(self.workspace, count=5, language='swh_KE')

        p = self.views.get_page(None, 'test-page-1', 'eng_UK')
        self.assertEqual(p.title, 'Test Page 1')
        self.assertEqual(p.language, 'eng_UK')

        p = self.views.get_page(None, 'test-page-1', 'swh_KE')
        self.assertEqual(p.language, 'swh_KE')

        with self.assertRaises(HTTPNotFound):
            p = self.views.get_page(None, 'invalid-slug')

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
        self.workspace.setup_custom_mapping(Page, {
            'properties': {
                'slug': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'language': {
                    'type': 'string',
                }
            }
        })

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
            self.workspace, language='eng_UK')
        category3, category4 = self.create_categories(
            self.workspace, language='swh_KE')

        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([category1.uuid, category2.uuid]),
            set([category.uuid
                 for category in self.views.get_categories()])
        )

        # Change language
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))
        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swh_KE', 'swh_KE']))

    def test_get_category(self):
        [category] = self.create_categories(
            self.workspace, count=1, language='swh_KE')
        [page] = self.create_pages(
            self.workspace, count=1, language='swh_KE',
            primary_category=category.uuid)

        request = testing.DummyRequest({'_LOCALE_': 'swh_KE'})
        request.matchdict['category'] = category.uuid
        views = CmsViews(request)
        response = views.category()
        self.assertEqual(response['category'].uuid, category.uuid)
        self.assertEqual(
            [p.uuid for p in response['pages']], [page.uuid])

    def test_get_top_nav(self):
        category1, category2 = self.create_categories(self.workspace)
        category3, category4 = self.create_categories(
            self.workspace, language='swh_KE', featured_in_navbar=True)

        self.assertEqual([], list(self.views.get_top_nav))

        # Change language
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))
        cat1, cat2 = self.views.get_top_nav
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swh_KE', 'swh_KE']))
