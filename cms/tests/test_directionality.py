from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings

from cms import locale_negotiator_with_fallbacks
from cms.tests.base import UnicoreTestCase
from cms.views.cms_views import CmsViews

from unicore.content.models import Page, Category, Localisation


class TestDirectionality(UnicoreTestCase):

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

        languages = "[('eng_GB', 'English'), ('urd_IN', 'Urdu')]"
        settings = {
            'git.path': self.workspace.repo.working_dir,
            'git.content_repo_url': '',
            'es.index_prefix': self.workspace.index_prefix,
            'cache.enabled': 'false',
            'cache.regions': 'long_term, default_term',
            'cache.long_term.expire': '1',
            'cache.default_term.expire': '1',
            'available_languages': languages,
            'pyramid.default_locale_name': 'eng_GB',
            'thumbor.security_key': 'sample-security-key',
            'thumbor.server': 'http://some.site.com',
        }
        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)
        self.views = CmsViews(testing.DummyRequest())
        self.app = self.mk_app(self.workspace, settings=settings)

    def test_ltr(self):
        [category1] = self.create_categories(
            self.workspace, count=1, locale='eng_GB', title='English Category')

        resp = self.app.get('/', status=200)
        self.assertTrue(
            'dir="ltr"'
            in resp.body)

    def test_rtl(self):
        loc = Localisation({
            'locale': 'urd_IN',
            'image': 'sample-uuid-000000-0001',
            'image_host': 'http://some.site.com/'})
        self.workspace.save(loc, 'Add localisation')
        self.workspace.refresh_index()

        request = testing.DummyRequest({'_LOCALE_': 'urd_IN'})
        self.views = CmsViews(request)

        localisation = self.views.get_localisation()
        self.assertEqual(localisation.locale, 'urd_IN')
