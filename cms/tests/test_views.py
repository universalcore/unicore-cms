import arrow
from datetime import timedelta
import os

from gitmodel import exceptions

from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings

from cms.views import CmsViews
from cms.tests.utils import BaseTestCase, RepoHelper


class TestViews(BaseTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.repo = RepoHelper.create(
            os.path.join(os.getcwd(), '.test_repos', self.id()))
        languages = "[('eng_UK', 'English'), ('swh_KE', 'Swahili (Kenya)')]"
        settings = {
            'git.path': self.repo.path,
            'git.content_repo_url': '',
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
        self.repo.destroy()
        testing.tearDown()

    def test_get_featured_pages(self):
        pages = self.repo.create_pages(
            count=10,
            timestamp_cb=lambda i: (
                arrow.utcnow() - timedelta(days=i)).isoformat())

        for page in pages[8:]:
            page.featured = True
            page.save(True, message='Make featured')

        featured_pages = self.views.get_featured_pages(limit=10)
        self.assertEqual(
            ['Test Page 9', 'Test Page 8'],
            [p.title for p in featured_pages])

    def test_get_pages_count(self):
        self.repo.create_pages(count=10)
        pages = self.views.get_pages(limit=7)
        self.assertEqual(len(pages), 7)

    def test_get_pages_order_by(self):
        self.repo.create_pages(count=10)
        pages = self.views.get_pages(limit=2, order_by=('title',))
        self.assertEqual(
            [p.title for p in pages],
            ['Test Page 0', 'Test Page 1'])

    def test_get_pages_reversed(self):
        self.repo.create_pages(
            count=10,
            timestamp_cb=lambda i: (
                arrow.utcnow() - timedelta(days=i)).isoformat())
        pages = self.views.get_pages(limit=2, reverse=True)
        self.assertEqual(
            [p.title for p in pages],
            ['Test Page 0', 'Test Page 1'])

    def test_get_available_languages(self):
        languages = self.views.get_available_languages
        self.assertEqual(languages[0][0], 'eng_UK')
        self.assertEqual(languages[1][0], 'swh_KE')
        self.assertEqual(languages[1][1], 'Swahili (Kenya)')

    def test_get_featured_category_pages(self):
        category1, category2 = self.repo.create_categories()
        pages = self.repo.create_pages(count=10)

        for page in pages[:8]:
            page.primary_category = category1
            page.save(True, message='Added category.')

        for page in pages[8:]:
            page.primary_category = category1
            page.featured_in_category = True
            page.save(True, message='Added category & set featured.')

        page1, page2 = self.views.get_featured_category_pages(category1.uuid)
        self.assertEqual(
            set([page1.title, page2.title]),
            set(['Test Page 8', 'Test Page 9']))
        self.assertEqual(
            set([page1.language, page2.language]),
            set(['eng_UK', 'eng_UK']))
        self.assertEqual(
            [], self.views.get_featured_category_pages(category2.uuid))

    def test_get_featured_category_pages_swahili(self):
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))

        category1, category2 = self.repo.create_categories()
        category3, category4 = self.repo.create_categories(
            [u'Dog', u'Cat'], 'swh_KE')
        pages = self.repo.create_pages(count=10)
        pages_swh = self.repo.create_pages(count=10, locale='swh_KE')

        # Default english pages
        for page in pages[:8]:
            page.primary_category = category1
            page.save(True, message='Added category.')

        for page in pages[8:]:
            page.primary_category = category1
            page.featured_in_category = True
            page.save(True, message='Added category & set featured.')

        # Pages in swahili
        for page in pages_swh[:8]:
            page.primary_category = category3
            page.save(True, message='Added category.')

        for page in pages_swh[8:]:
            page.primary_category = category3
            page.featured_in_category = True
            page.save(True, message='Added category & set featured.')

        # Assert english content not returned since language is swahili
        self.assertEqual(
            [], self.views.get_featured_category_pages(category1.uuid))

        # Assert swahili content
        page1, page2 = self.views.get_featured_category_pages(category3.uuid)
        self.assertEqual(
            set([page1.language, page2.language]),
            set(['swh_KE', 'swh_KE']))
        self.assertEqual(
            [], self.views.get_featured_category_pages(category4.uuid))

    def test_get_page_by_slug(self):
        self.repo.create_pages(count=5)
        self.repo.create_pages(count=5, locale='swh_KE')
        p = self.views.get_page(None, 'test-page-1', 'eng_UK')
        self.assertEqual(p.title, 'Test Page 1')
        self.assertEqual(p.language, 'eng_UK')

        p = self.views.get_page(None, 'test-page-1', 'swh_KE')
        self.assertEqual(p.language, 'swh_KE')

        with self.assertRaises(exceptions.DoesNotExist):
            p = self.views.get_page(None, 'invalid-slug')

    def test_content_markdown_rendering(self):
        [page] = self.repo.create_pages(count=1)
        page.content = '**strong**'
        page.description = '_emphasised_'
        page.save(True, message='Add markdown markup')

        request = testing.DummyRequest()
        request.matchdict['uuid'] = page.uuid
        self.views = CmsViews(request)
        response = self.views.content()
        self.assertEqual(
            response['content'], '<p><strong>strong</strong></p>')
        self.assertEqual(
            response['description'], '<p><em>emphasised</em></p>')

    def test_flatpage_markdown_rendering(self):
        [page] = self.repo.create_pages(count=1)
        page.content = '**strong**'
        page.description = '_emphasised_'
        page.save(True, message='Add markdown markup')

        request = testing.DummyRequest()
        request.matchdict['slug'] = page.slug
        self.views = CmsViews(request)
        response = self.views.flatpage()
        self.assertEqual(
            response['content'], '<p><strong>strong</strong></p>')
        self.assertEqual(
            response['description'], '<p><em>emphasised</em></p>')

    def test_get_categories(self):
        category1, category2 = self.repo.create_categories()
        category3, category4 = self.repo.create_categories(
            [u'Dog', u'Cat'], 'swh_KE')

        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['eng_UK', 'eng_UK']))

        # Change language
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))
        cat1, cat2 = self.views.get_categories()
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swh_KE', 'swh_KE']))

    def test_get_category(self):
        category, _ = self.repo.create_categories([u'dog', u'cat'], 'swh_KE')
        [page] = self.repo.create_pages(count=1, locale='swh_KE')
        page.primary_category = category
        page.save(True, message="Adding category.")

        request = testing.DummyRequest({'_LOCALE_': 'swh_KE'})
        request.matchdict['category'] = category.uuid
        views = CmsViews(request)
        response = views.category()
        self.assertEqual(response['category'].uuid, category.uuid)
        self.assertEqual(
            [p.uuid for p in response['pages']], [page.uuid])

    def test_get_top_nav(self):
        category1, category2 = self.repo.create_categories()
        category3, category4 = self.repo.create_categories(
            [u'Dog', u'Cat'], 'swh_KE', featured_in_navbar=True)

        self.assertEqual([], self.views.get_top_nav)

        # Change language
        self.views = CmsViews(testing.DummyRequest({'_LOCALE_': 'swh_KE'}))
        cat1, cat2 = self.views.get_top_nav
        self.assertEqual(
            set([cat1.language, cat2.language]),
            set(['swh_KE', 'swh_KE']))
