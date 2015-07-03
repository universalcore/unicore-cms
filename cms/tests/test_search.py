from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings

from cms import locale_negotiator_with_fallbacks

from cms.tests.base import UnicoreTestCase
from unicore.content.models import Page, Category, Localisation


class TestSearch(UnicoreTestCase):

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

        settings = self.get_settings(
            self.workspace,
            available_languages=languages,
            featured_languages=featured_langs)

        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)

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

    def test_search_single_language_results(self):
        mother_english = Page({
            'title': 'title for english mother', 'language': 'eng_GB',
            'position': 2, 'content': 'Page for mother test page'})
        mother_spanish = Page({
            'title': 'title for spanish mother', 'language': 'spa_ES',
            'position': 2, 'content': 'Page for mother test page'})
        self.workspace.save(mother_english, 'Add mother page')
        self.workspace.save(mother_spanish, 'Add mother page')

        self.workspace.refresh_index()

        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)

        self.assertTrue('title for english mother' in resp.body)
        self.assertTrue('1 search result' in resp.body)
        self.assertFalse('No results found' in resp.body)

        self.app.get('/locale/spa_ES/', status=302)
        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)
        self.assertTrue('title for spanish mother' in resp.body)
        self.assertTrue('1 search result' in resp.body)
        self.assertFalse('No results found' in resp.body)

    def test_search_single_language_no_results(self):
        mother_english = Page({
            'title': 'title for english mother', 'language': 'eng_GB',
            'position': 2, 'content': 'Page for mother test page'})
        self.workspace.save(mother_english, 'Add mother page')
        self.workspace.refresh_index()

        self.app.get('/locale/spa_ES/', status=302)
        resp = self.app.get('/search/', params={'q': 'mother'}, status=200)
        self.assertTrue('No results found' in resp.body)
