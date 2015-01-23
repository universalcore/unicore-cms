from pyramid import testing

from cms.tests.base import UnicoreTestCase
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
        self.app = self.mk_app(self.workspace, settings=settings)

    def test_search_no_results(self):
        self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': ''}, status=200)
        self.assertTrue('No results found' in resp.body)

    def test_search_blank(self):
        self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': None}, status=200)
        self.assertTrue('No results found' in resp.body)

    def test_search_2_results(self):
        self.create_pages(self.workspace, count=2)
        resp = self.app.get('/search/', params={'q': 'sample'}, status=200)

        self.assertFalse('No results found' in resp.body)
        self.assertTrue('Test Page 0' in resp.body)
        self.assertTrue('Test Page 1' in resp.body)

    def test_search_multiple_results(self):
        self.create_pages(self.workspace, count=50)
        resp = self.app.get('/search/', params={'q': 'sample'}, status=200)
        self.assertTrue(
            '<a href="/search/?q=sample&p=1">&nbsp;Next&nbsp;&gt;</a>'
            in resp.body)

    def test_search_profanity(self):
        self.create_pages(self.workspace, count=2)

        resp = self.app.get('/search/', params={'q': 'kak'}, status=200)

        self.assertTrue('No results found' in resp.body)

    def test_search_added_page(self):
        mother_page = Page({
            'title': 'title for mother', 'language': 'eng_GB', 'position': 2,
            'content': 'Page for mother test page'})
        self.workspace.save(mother_page, 'Add mother page')

        self.workspace.refresh_index()

        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)

        self.assertTrue('mother' in resp.body)
        self.assertFalse('No results found' in resp.body)

    def test_pagination(self):
        self.create_pages(self.workspace, count=15, content='baby')
        resp = self.app.get(
            '/search/', params={'q': 'baby', 'p': '0'}, status=200)
        self.assertFalse('Previous' in resp.body)
        self.assertTrue('Next' in resp.body)
