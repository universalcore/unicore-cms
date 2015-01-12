import uuid

from elasticgit import EG
from dateutil import parser
from libthumbor import CryptoURL
from cms.tasks import send_ga_pageview


class BaseCmsView(object):

    def __init__(self, request):
        self.request = request
        self.locale = request.locale_name
        self.settings = request.registry.settings
        self.workspace = EG.workspace(
            workdir=self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'])
        self.track_pageview()

    def format_date(self, date_str, fmt='%d %B %Y'):
        try:
            dt = parser.parse(date_str)
            return dt.strftime(fmt)
        except TypeError:
            return date_str
        except ValueError:
            return date_str

    def get_image_url(self, image_host, image_uuid, width=None, height=None):
        security_key = self.settings.get('thumbor.security_key')
        if not (security_key and image_host and image_uuid):
            return ''

        crypto = CryptoURL(key=security_key)

        if not (width or height):
            image_url = crypto.generate(image_url=image_uuid)
        elif width and height:
            image_url = crypto.generate(
                width=width, height=height, image_url=image_uuid)
        elif width:
            image_url = crypto.generate(
                width=width, height=0, image_url=image_uuid)
        else:
            image_url = crypto.generate(
                width=0, height=height, image_url=image_uuid)

        return u'%s%s' % (image_host, image_url)

    def get_or_create_ga_client_id(self):
        '''
        NOTE: client_id can be any unique identifier.
              UniversalAnalytics converts any client_id to a
              UUID4-format MD5 checksum. This means we can safely use
              a UID provided by FB as a client_id and GA will track
              accurately.
        '''

        client_id = self.request.cookies.get('ga_client_id')
        if client_id:
            return client_id
        client_id = str(uuid.uuid4())
        self.request.response.set_cookie(
            'ga_client_id', value=client_id, max_age=31536000)
        return client_id

    def track_pageview(self):
        profile_id = self.settings.get('ga.profile_id')
        if profile_id:
            send_ga_pageview.delay(
                profile_id,
                self.get_or_create_ga_client_id(),
                self.request.path,
                self.request.remote_addr,
                self.request.referer or '',
                self.request.domain,
                self.request.user_agent)
