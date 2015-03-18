import re
import json
from urlparse import urlparse, parse_qs
from urllib import urlencode

from pyramid import testing
from pyramid.interfaces import IAuthenticationPolicy
from pyramid_beaker import set_cache_regions_from_settings

from beaker.session import Session
import responses
import webob
import mock
from webtest import TestRequest

from cms import USER_DATA_SESSION_KEY
from cms.tests.base import UnicoreTestCase
from cms.views.cms_views import CmsViews


class TestAuth(UnicoreTestCase):

    def setUp(self):
        self.workspace = self.mk_workspace()
        settings = self.get_settings(self.workspace)

        self.config = testing.setUp(settings=settings)
        self.config.include('cms')
        set_cache_regions_from_settings(settings)

        self.views = CmsViews(testing.DummyRequest())
        self.app = self.mk_app(self.workspace, settings=settings)

    def tearDown(self):
        testing.tearDown()

    def test_redirect_to_login(self):
        url = '/login/hub/?%s' % urlencode({'_LOCALE_': 'urd_IN'})

        request_with_all = TestRequest.blank(
            url, method='GET', referrer='http://localhost/content/list/')
        request_without_ref = TestRequest.blank(url, method='GET')
        request_with_invalid_ref = TestRequest.blank(
            url, method='GET', referrer='http://example.com/page/')

        for request in (request_with_all,
                        request_without_ref,
                        request_with_invalid_ref):
            resp = self.app.request(request)

            self.assertEqual(resp.status_int, 302)

            parts = urlparse(resp.location)
            params = parse_qs(parts.query)
            self.assertIn('service', params)
            self.assertIn('_LOCALE_', params)
            self.assertEqual(params['_LOCALE_'][0], request.params['_LOCALE_'])

            callback_url = params['service'][0]
            parts = urlparse(callback_url)
            self.assertEqual(parts[:3], ('http', 'localhost', '/login/'))

            if request is request_with_all:
                params = parse_qs(parts.query)
                self.assertIn('url', params)
                self.assertEqual(
                    params['url'][0], request.referrer)
            else:
                self.assertFalse(parts.query)

    @responses.activate
    def test_login(self):
        ticket = 'iamaticket'
        redirect_url = 'http://localhost/content/list/'
        user_data = {
            'uuid': 'imauuid',
            'username': 'foo',
            'app_data': {'display_name': 'foobar'}
        }

        responses.add(
            responses.GET, re.compile(r'.*/sso/validate.*'),
            body=json.dumps(user_data),
            status=200,
            content_type='application/json')

        request_with_url = TestRequest.blank(
            '/login/?%s' % urlencode({'ticket': ticket, 'url': redirect_url}))
        request_without_url = TestRequest.blank(
            '/login/?%s' % urlencode({'ticket': ticket}))

        for request in (request_with_url, request_without_url):
                resp = self.app.request(request)

                self.assertEqual(resp.status_int, 302)
                if request == request_with_url:
                    self.assertEqual(resp.location, redirect_url)
                else:
                    self.assertEqual(resp.location, 'http://localhost/')

                # check that session contains user data
                self.assertIn('beaker.session.id', self.app.cookies)
                session = Session(
                    request,
                    id=self.app.cookies['beaker.session.id'],
                    use_cookies=False)
                self.assertEqual(session['auth.userid'], user_data['uuid'])
                self.assertEqual(session[USER_DATA_SESSION_KEY], user_data)

                self.app.reset()

        responses.reset()
        responses.add(
            responses.GET, re.compile(r'.*/sso/validate.*'),
            body=json.dumps('no\n'), status=200,
            content_type='application/json')

        resp = self.app.request(request_with_url)
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.location, redirect_url)
        self.assertNotIn('beaker.session.id', self.app.cookies)

    def test_auth_policy(self):
        user_data = {
            'uuid': 'imauuid',
            'username': 'foo',
            'app_data': {'display_name': 'foobar'}
        }
        request = testing.DummyRequest()

        session = Session(request, id='imabeakerid', use_cookies=False)
        session[USER_DATA_SESSION_KEY] = user_data
        session['auth.userid'] = user_data['uuid']
        request.session = session

        auth_policy = self.app.app.registry.queryUtility(IAuthenticationPolicy)
        self.assertEqual(
            auth_policy.callback('imauuid', request), ('imauuid', ))

    def test_user_on_request(self):
        user_data = {
            'uuid': 'imauuid',
            'username': 'foo',
            'app_data': {'display_name': 'foobar'}
        }
        session = Session(
            testing.DummyRequest(), id='imabeakerid', use_cookies=False)
        session[USER_DATA_SESSION_KEY] = user_data
        session['auth.userid'] = user_data['uuid']
        session.save()
        session = Session(
            testing.DummyRequest(), id='imabeakerid2', use_cookies=False)
        session.save()

        request_auth = webob.Request.blank('/')
        request_auth.headers['Cookie'] = 'beaker.session.id=imabeakerid'
        request_no_auth = webob.Request.blank('/')
        request_no_auth.headers['Cookie'] = 'beaker.session.id=imabeakerid2'

        with mock.patch.object(self.app.app, 'handle_request') as mock_handler:
            mock_handler.return_value = mock.Mock()
            self.app.app(request_auth.environ, None)
            self.app.app(request_no_auth.environ, None)
            internal_request_auth = mock_handler.call_args_list[0][0][0]
            internal_request_no_auth = mock_handler.call_args_list[1][0][0]

        self.assertTrue(hasattr(internal_request_auth, 'user'))
        self.assertEqual(internal_request_auth.user.data, user_data)
        self.assertTrue(hasattr(internal_request_no_auth, 'user'))
        self.assertEqual(internal_request_no_auth.user, None)
