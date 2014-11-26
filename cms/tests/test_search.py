from pyramid import testing

from cms.tests.base import UnicoreTestCase
from cms import main
from webtest import TestApp


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
        #self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': ''}, status=200)
        self.assertTrue('No results found!' in resp.body)

    def test_search_2_results(self):
        self.create_pages(self.workspace, count=2)
        resp = self.app.get('/search/', params={'q': 'sample'}, status=200)

        self.assertFalse('No results found!' in resp.body)
        self.assertTrue('Test Page 0' in resp.body)
        self.assertTrue('Test Page 1' in resp.body)

    def test_search_profanity(self):

        resp = self.app.get('/search/', params={'q':'kak'}, status=200)

        self.assertTrue('a' in resp.body)
        self.assertFalse('kak' in resp.body)
     
     #data specific
    def test_search_3_results(self):

        self.create_pages(self.workspace, count=2)
        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)
        
        #print resp.body

        self.assertTrue('a' in resp.body)
        self.assertFalse('No results found!' in resp.body)
        