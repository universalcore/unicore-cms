import time
from unittest import TestCase
from datetime import datetime
from dateutil import parser as dt_parser
import pytz

import mock
from deform import ValidationFailure

from pyramid import testing

from unicore.hub.client import User
from unicore.comments.client import CommentClient
from unicore.content.models import Page
from cms.tests.base import UnicoreTestCase
from cms.views.forms import CommentForm, COMMENT_STALE_AFTER


class TestCommentViews(UnicoreTestCase):
    pass


class TestCommentForm(TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.route_url = mock.Mock(return_value='content_url')
        self.request.locale_name = 'eng_GB'
        self.request.user = User(None, {
            'uuid': 'user_uuid',
            'app_data': {'display_name': 'Foo'}})
        self.request.session = mock.Mock(
            get_csrf_token=mock.Mock(return_value='csrf_foo'))
        self.request.registry.commentclient = CommentClient(
            app_id='app_uuid', host='host_url')
        self.content_object = Page({
            'uuid': 'content_uuid',
            'title': 'content_title'})
        self.form = CommentForm(self.request, self.content_object)

    def test_no_comment_client(self):
        self.request.registry.commentclient = None
        self.assertRaisesRegexp(
            ValueError, 'No comment client configured', self.form.validate, {})

    def test_no_user(self):
        self.request.user = None
        self.assertRaisesRegexp(
            ValueError, 'No authenticated user', self.form.validate, {})

    def test_security_errors(self):
        cstruct = {
            'comment': 'foo',
            'content_type': 'page',
            'content_uuid': 'content_uuid',
            'timestamp': int(time.time()),
            'csrf': 'csrf_foo'
        }

        def check_error(field, *invalid_values):
            data = cstruct.copy()
            for invalid, msg in invalid_values:
                if invalid == '__del__':
                    del data[field]
                else:
                    data[field] = invalid
                self.assertRaisesRegexp(
                    ValueError, msg, self.form.validate, data.items())

        check_error(
            'content_type',
            ('does_not_match', 'Invalid content type'),
            ('__del__', 'Required'))
        check_error(
            'content_uuid',
            ('does_not_match', 'Invalid content uuid'),
            ('__del__', 'Required'))
        check_error(
            'timestamp',
            ('wrong_type', 'is not a number'),
            (int(time.time()) - COMMENT_STALE_AFTER - 1,
                'Timestamp check failed'),
            ('__del__', 'Required'))
        check_error(
            'csrf',
            ('does_not_match', 'Bad CSRF token'),
            ('__del__', 'Required'))

    def test_validation_failure(self):
        cstruct = {
            'content_type': 'page',
            'content_uuid': 'content_uuid',
            'timestamp': int(time.time()),
            'csrf': 'csrf_foo'
        }
        self.assertRaises(
            ValidationFailure, self.form.validate, cstruct.items())
        cstruct['comment'] = ''
        self.assertRaises(
            ValidationFailure, self.form.validate, cstruct.items())

    def test_returned_data(self):
        cstruct = {
            'comment': 'this is a comment',
            'content_type': 'page',
            'content_uuid': 'content_uuid',
            'timestamp': int(time.time()),
            'csrf': 'csrf_foo'
        }
        data = self.form.validate(cstruct.items())

        submit_datetime = data.pop('submit_datetime', None)
        self.assertEqual(
            dt_parser.parse(submit_datetime).date(),
            datetime.now(pytz.utc).date())
        self.assertEqual(data, {
            'app_uuid': 'app_uuid',
            'content_uuid': 'content_uuid',
            'user_uuid': 'user_uuid',
            'comment': 'this is a comment',
            'user_name': 'Foo',
            'content_type': 'page',
            'content_title': 'content_title',
            'content_url': 'content_url',
            'locale': 'eng_GB'
        })

        del self.request.user.get('app_data')['display_name']
        data = self.form.validate(cstruct.items())

        self.assertEqual(data.get('user_name'), 'Anonymous')
