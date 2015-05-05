import time
from datetime import datetime
import pytz

import colander
from deform import Form, widget, ValidationFailure

from unicore.content.models import Page
from utils import translation_string_factory as _


COMMENT_MAX_LENGTH = 3000
COMMENT_STALE_AFTER = 2 * 60 * 60  # 2 hours
COMMENT_CONTENT_TYPES = {
    Page: 'page'
}


'''
Defaults
'''


@colander.deferred
def deferred_timestamp_default(node, kw):
    return int(time.time())


@colander.deferred
def deferred_content_uuid_default(node, kw):
    content_object = kw['content_object']
    return content_object.uuid


@colander.deferred
def deferred_content_type_default(node, kw):
    content_object = kw['content_object']
    return COMMENT_CONTENT_TYPES[content_object.__class__]


@colander.deferred
def deferred_csrf_default(node, kw):
    request = kw.get('request')
    csrf_token = request.session.get_csrf_token()
    return csrf_token


'''
Validators
'''


@colander.deferred
def deferred_csrf_validator(node, kw):
    def validate_csrf(node, value):
        request = kw.get('request')
        csrf_token = request.session.get_csrf_token()
        if value != csrf_token:
            raise ValueError('Bad CSRF token')
    return validate_csrf


@colander.deferred
def deferred_content_uuid_validator(node, kw):
    def validate_content_uuid(node, value):
        content_object = kw['content_object']
        if content_object.uuid != value:
            raise colander.Invalid(node, 'Invalid content uuid')
    return validate_content_uuid


@colander.deferred
def deferred_content_type_validator(node, kw):
    def validate_content_type(node, value):
        content_object = kw['content_object']
        if COMMENT_CONTENT_TYPES[content_object.__class__] != value:
            raise colander.Invalid(node, 'Invalid content type')
    return validate_content_type


def validate_comment_timestamp(node, value):
    if time.time() - value > COMMENT_STALE_AFTER:
        raise colander.Invalid(node, 'Timestamp check failed')


'''
Schemata
'''


class CSRFSchema(colander.MappingSchema):
    ''' Adapted from http://deformdemo.repoze.org/pyramid_csrf_demo/
    '''
    csrf = colander.SchemaNode(
        colander.String(),
        default=deferred_csrf_default,
        validator=deferred_csrf_validator,
        widget=widget.HiddenWidget())


class CommentSchema(CSRFSchema):
    comment = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=COMMENT_MAX_LENGTH),
        widget=widget.TextAreaWidget(),
        title=_('Comment'))
    content_uuid = colander.SchemaNode(
        colander.String(),
        default=deferred_content_uuid_default,
        validator=deferred_content_uuid_validator,
        widget=widget.HiddenWidget())
    content_type = colander.SchemaNode(
        colander.String(),
        default=deferred_content_type_default,
        validator=deferred_content_type_validator,
        widget=widget.HiddenWidget())
    timestamp = colander.SchemaNode(
        colander.Integer(),
        default=deferred_timestamp_default,
        validator=validate_comment_timestamp,
        widget=widget.HiddenWidget())


'''
Forms
'''


class CommentForm(Form):

    def __init__(self, request, content_object):
        self.schema = CommentSchema().bind(
            request=request,
            content_object=content_object)
        self.request = request
        self.content_object = content_object

        super(CommentForm, self).__init__(self.schema)

    def validate(self, cstruct):
        c_client = self.request.registry.commentclient
        user = self.request.user
        if not c_client:
            raise ValueError('No comment client configured')
        if not user:
            raise ValueError('No authenticated user')

        try:
            appstruct = super(CommentForm, self).validate(cstruct)
        except ValidationFailure as e:
            # re-raise security errors as ValueError
            security_fields = {
                'content_type', 'content_uuid', 'timestamp', 'csrf'}
            for field, msg in e.error.asdict().iteritems():
                if field in security_fields:
                    raise ValueError(msg)
            raise e

        data = {
            'app_uuid': c_client.settings['app_id'],
            'content_uuid': appstruct['content_uuid'],
            'user_uuid': user.get('uuid'),
            'comment': appstruct['comment'],
            'user_name': user.get('app_data').get(
                'display_name', _('Anonymous')),
            'submit_datetime': datetime.now(pytz.utc).isoformat(),
            'content_type': appstruct['content_type'],
            'content_title': self.content_object.title,
            'content_url': self.request.route_url(
                'content', uuid=self.content_object.uuid),
            'locale': self.request.locale_name,
        }
        return data
