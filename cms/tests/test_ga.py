import mock

from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings

from cms import locale_negotiator_with_fallbacks
from cms.tests.base import UnicoreTestCase

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

        languages = "[('eng_GB', 'English'), ('swa_KE', 'Swahili (Kenya)')]"
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
            'ga.profile_id': 'UA-some-id',
        }
        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)
        env = {'REMOTE_ADDR': '192.0.0.1'}

        self.app = self.mk_app(
            self.workspace, settings=settings, extra_environ=env)

    def tearDown(self):
        testing.tearDown()

    @mock.patch('unicore.google.tasks.pageview.delay')
    def test_ga_pageviews(self, mock_delay):
        [category] = self.create_categories(self.workspace, count=1)
        page1 = Page({
            'title': 'title 1', 'language': 'eng_GB', 'position': 3,
            'primary_category': category.uuid, 'content': 'some text',
            'description': 'some description'})
        self.workspace.save(page1, 'Add page')
        self.workspace.refresh_index()

        self.app.get('/', status=200, headers={
            'Accept-Language': 'en',
            'User-Agent': 'Mozilla/5.0',
        }, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })

        mock_delay.assert_called_once()
        (profile_id, gen_client_id, data), _ = mock_delay.call_args_list[0]

        self.assertEqual(profile_id, 'UA-some-id')
        self.assertEqual(data, {
            'path': '/',
            'uip': '192.0.0.1',
            'dr': '',
            'dh': 'some.site.com',
            'user_agent': 'Mozilla/5.0',
            'ul': 'en',
        })

        page_url = '/content/detail/%s/' % page1.uuid
        self.app.get(page_url, status=200, headers={
            'User-agent': 'Mozilla/5.0',
            'Accept-Language': 'en',
        }, extra_environ={
            'HTTP_REFERER': '/',
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })

        (profile_id, client_id, data), _ = mock_delay.call_args_list[1]
        self.assertEqual(profile_id, 'UA-some-id')
        self.assertEqual(data, {
            'path': page_url,
            'uip': '192.0.0.1',
            'dr': '/',
            'dh': 'some.site.com',
            'user_agent': 'Mozilla/5.0',
            'ul': 'en',
        })

        self.assertEqual(gen_client_id, client_id)
