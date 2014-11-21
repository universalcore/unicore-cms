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

    def test_search(self):
        self.create_categories(self.workspace)
        self.create_pages(self.workspace)

        resp = self.app.get('/search/', params={'q': 'some query'}, status=200)

        # This will test that the results page shows this message when
        # a search returns no results
        self.assertTrue('No results found!' in resp.body)
