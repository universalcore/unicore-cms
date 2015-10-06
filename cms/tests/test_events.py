from datetime import datetime
from collections import namedtuple

import mock

from cms.tests.base import UnicoreTestCase
from cms.events import new_request


class TestEvents(UnicoreTestCase):

    def setUp(self):
        self.workspace = self.mk_workspace()
        settings = self.get_settings(self.workspace)
        settings['ga.profile_id'] = 'UA-some-id'
        self.app = self.mk_app(self.workspace, settings=settings)
        [self.category] = self.create_categories(self.workspace, count=1)
        [self.page] = self.create_pages(
            self.workspace, count=1,
            primary_category=self.category.uuid,
            created_at=datetime.now().isoformat(),
            description='')

    def test_new_request_event_no_profile_id(self):
        Event = namedtuple('Event', ['request', 'response'])
        Registry = namedtuple('Registry', ['settings'])
        request = self.mk_request()
        request.registry = Registry(settings={})
        new_request(Event(request=request, response=None))
        self.assertEqual(request.google_analytics, {})

    def test_new_request_event(self):
        Event = namedtuple('Event', ['request', 'response'])
        Registry = namedtuple('Registry', ['settings'])
        request = self.mk_request()
        request.remote_addr = 'remote_addr'
        request.referer = 'referer'
        request.user_agent = 'user_agent'
        request.accept_language = 'language'
        request.registry = Registry(settings={
            'ga.profile_id': 'foo',
        })
        new_request(Event(request=request, response=None))
        self.assertEqual(request.google_analytics, {
            'dh': 'example.com',
            'dr': 'referer',
            'path': '/',
            'uip': 'remote_addr',
            'ul': 'language',
            'user_agent': 'user_agent',
        })

    @mock.patch('unicore.google.tasks.pageview.delay')
    def test_ga_pageviews(self, mock_task):

        self.app.get('/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 1)
        ((profile_id, gen_client_id, data), _) = mock_task.call_args_list[0]
        self.assertEqual(profile_id, 'UA-some-id')
        self.assertEqual(data['path'], '/')
        self.assertEqual(data['uip'], '192.0.0.1')
        self.assertEqual(data['dh'], 'some.site.com')
        self.assertEqual(data['dr'], '')

        page_url = '/content/detail/%s/' % (self.page.uuid,)
        headers = {
            'User-agent': 'Mozilla/5.0',
        }
        self.app.get(page_url, status=200, headers=headers, extra_environ={
            'HTTP_REFERER': '/',
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        ((profile_id, client_id, data), _) = mock_task.call_args_list[1]

        self.assertEqual(profile_id, 'UA-some-id')
        self.assertEqual(data['path'], page_url)
        self.assertEqual(data['dr'], '/')
        self.assertEqual(data['uip'], '192.0.0.1')
        self.assertEqual(data['dh'], 'some.site.com')
        self.assertEqual(data['user_agent'], 'Mozilla/5.0')
        self.assertEqual(data['dt'], self.page.title)

        # # ensure cid is the same across calls
        self.assertEqual(gen_client_id, client_id)

    @mock.patch('unicore.google.tasks.pageview.delay')
    def test_ga_context_decorator(self, mock_task):
        page_url = '/content/detail/%s/' % (self.page.uuid,)
        category_url = '/content/list/%s/' % (self.category.uuid,)
        headers = {
            'User-agent': 'Mozilla/5.0',
        }
        self.app.get(category_url, status=200, headers=headers, extra_environ={
            'HTTP_REFERER': '/',
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        ((profile_id, client_id, data), _) = mock_task.call_args_list[0]
        self.assertEqual(data['dt'], self.category.title)

        self.app.get(page_url, status=200, headers=headers, extra_environ={
            'HTTP_REFERER': category_url,
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        ((profile_id, client_id, data), _) = mock_task.call_args_list[1]
        self.assertEqual(data['dt'], self.page.title)

    @mock.patch('unicore.google.tasks.pageview.delay')
    def test_ga_pageviews_excluded_paths(self, mock_task):

        self.app.get('/health/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 0)

        self.app.post('/api/notify/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 0)

    @mock.patch('unicore.google.tasks.pageview.delay')
    def test_ga_pageviews_excluded_paths_in_settings(self, mock_task):
        self.app.post('/locale/change/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 1)

        # add locale change to excluded path for testing

        settings = self.get_settings(self.workspace)
        settings['ga.profile_id'] = 'UA-some-id'
        settings['ga.excluded_paths'] = '/locale/change/,/search/'
        self.app = self.mk_app(self.workspace, settings=settings)

        self.app.post('/locale/change/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 1)

        self.app.post('/search/', status=200, extra_environ={
            'HTTP_HOST': 'some.site.com',
            'REMOTE_ADDR': '192.0.0.1',
        })
        self.assertEqual(mock_task.call_count, 1)
