import urlparse
import mock

from pyramid import testing
from pyramid_beaker import set_cache_regions_from_settings
from webtest import TestApp

from cms import locale_negotiator_with_fallbacks, main
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
            'CELERY_ALWAYS_EAGER': True,
        }
        self.config = testing.setUp(settings=settings)
        set_cache_regions_from_settings(settings)
        self.config.set_locale_negotiator(locale_negotiator_with_fallbacks)
        env = {'REMOTE_ADDR': '192.0.0.1'}
        self.app = TestApp(main({}, **settings), extra_environ=env)

    def tearDown(self):
        testing.tearDown()

    @mock.patch('UniversalAnalytics.Tracker.urlopen')
    def test_ga_pageviews(self, mock_urlopen):
        [category] = self.create_categories(self.workspace, count=1)
        page1 = Page({
            'title': 'title 1', 'language': 'eng_GB', 'position': 3,
            'primary_category': category.uuid, 'content': 'some text',
            'description': 'some description'})
        self.workspace.save(page1, 'Add page')
        self.workspace.refresh_index()

        self.app.get('/', status=200, headers={'HOST': 'some.site.com'})
        mock_urlopen.assert_called_once()
        ((arg, ), _) = mock_urlopen.call_args_list[0]
        req = urlparse.parse_qs(arg.data)
        self.assertEqual(req['tid'], ['UA-some-id'])
        self.assertEqual(req['t'], ['pageview'])
        self.assertEqual(req['dp'], ['/'])
        self.assertEqual(req['uip'], ['192.0.0.1'])
        self.assertEqual(req['dh'], ['some.site.com'])
        self.assertIsNone(req.get('dr'))
        self.assertTrue(['cid'], req)

        [cid] = req['cid']  # save cid for later

        page_url = '/content/detail/%s/' % page1.uuid
        headers = {
            'REFERER': '/',
            'HOST': 'some.site.com',
            'User-agent': 'Mozilla/5.0'}
        self.app.get(page_url, status=200, headers=headers)
        ((arg, ), _) = mock_urlopen.call_args_list[1]

        req = urlparse.parse_qs(arg.data)
        self.assertEqual(req['tid'], ['UA-some-id'])
        self.assertEqual(req['t'], ['pageview'])
        self.assertEqual(req['dp'], [page_url])
        self.assertEqual(req['dr'], ['/'])
        self.assertEqual(req['uip'], ['192.0.0.1'])
        self.assertEqual(req['dh'], ['some.site.com'])
        self.assertEqual(arg.headers['User-agent'], 'Mozilla/5.0')

        # ensure cid is the same across calls
        self.assertEqual(req['cid'], [cid])
