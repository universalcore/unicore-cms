from pyramid import testing

from cms.tests.base import UnicoreTestCase
from cms import main
from cms.views.cms_views import CmsViews
from webtest import TestApp
from unicore.content.models import Page


class TestSearch(UnicoreTestCase):

    def setUp(self):
        self.workspace = self.mk_workspace()
        settings = {
            'git.path': self.workspace.working_dir,
            'git.content_repo_url': '',
            'es.index_prefix': self.workspace.index_prefix,
            'cache.enabled': 'false',
            'cache.regions': 'long_term, default_term',
            'cache.long_term.expire': '1',
            'cache.default_term.expire': '1',
            'pyramid.default_locale_name': 'eng_GB',
        }
        self.config = testing.setUp(settings=settings)
        self.app = TestApp(main({}, **settings))

    def test_search_no_results(self):
        self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': ''}, status=200)
        self.assertTrue('No results found!' in resp.body)

    def test_search_blank(self):
        self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': None}, status=200)
        self.assertTrue('No results found!' in resp.body)

    def test_search_2_results(self):
        self.create_pages(self.workspace, count=2)
        resp = self.app.get('/search/', params={'q': 'sample'}, status=200)

        self.assertFalse('No results found!' in resp.body)
        self.assertTrue('Test Page 0' in resp.body)
        self.assertTrue('Test Page 1' in resp.body)

    def test_search_profanity(self):
        self.create_pages(self.workspace, count=2)

        resp = self.app.get('/search/', params={'q': 'kak'}, status=200)

        self.assertTrue('No results found!' in resp.body)

    def test_search_added_page(self):
        mother_page = Page({
            'title': 'title for mother', 'language': 'eng_GB', 'position': 2,
            'content': 'Page for mother test page'})
        self.workspace.save(mother_page, 'Add mother page')

        self.workspace.refresh_index()

        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)

        self.assertTrue('mother' in resp.body)
        self.assertFalse('No results found!' in resp.body)

    def test_for_multiple_results_returned(self):
        pages = self.create_pages(
            self.workspace, count=5, content='Random content sample for fun',
            language='spa_ES')

        request = testing.DummyRequest({'_LOCALE_': 'spa_ES', 'q': 'fun'})
        self.views = CmsViews(request)
        search_results = self.views.search()['results']
        self.assertEqual(len(search_results), 5)
        self.assertEqual(
            set([p.title for p in pages]),
            set([p.title for p in search_results]))

    def test_no_previous_next_page(self):
        self.create_pages(self.workspace, count=5, content='baby')
        resp = self.app.get('/search/', params={'q': 'baby'}, status=200)
        self.assertFalse('Previous' in resp.body)
        self.assertFalse('Next' in resp.body)

    def test_next_page(self):
        self.create_pages(self.workspace, count=15, content='baby')
        resp = self.app.get('/search/', params={'q': 'baby'}, status=200)
        self.assertFalse('Previous' in resp.body)
        self.assertTrue('Next' in resp.body)

    def test_previous_page(self):
        self.create_pages(self.workspace, count=15, content='baby')
        resp = self.app.get(
            '/search/', params={'q': 'baby', 'p': '2'}, status=200)
        self.assertTrue('Previous' in resp.body)
        self.assertFalse('Next' in resp.body)

    def test_previous_and_next_page(self):
        self.create_pages(self.workspace, count=25, content='baby')
        resp = self.app.get(
            '/search/', params={'q': 'baby', 'p': '2'}, status=200)
        self.assertTrue('Previous' in resp.body)
        self.assertTrue('Next' in resp.body)
