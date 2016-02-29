from urlparse import urljoin
from datetime import datetime

from elasticgit import EG
from elasticgit.workspace import RemoteWorkspace
from dateutil import parser
from libthumbor import CryptoURL

from cms.views.utils import is_remote_repo_url, CachingRemoteStorageManager


# known Right to Left language codes
KNOWN_RTL = set(["urd", "ara", "arc", "per", "heb", "kur", "yid"])


class BaseCmsView(object):

    def __init__(self, request):
        self.request = request
        self.locale = request.locale_name
        self.settings = request.registry.settings
        self.es_settings = {'urls': [
            self.parse_setting('es.host', 'http://localhost:9200', unicode),
        ]}
        self.results_per_page = self.parse_setting(
            'results_per_page', 10, int)
        repo_url = self.settings['git.path']
        is_remote = is_remote_repo_url(repo_url)
        workspace_init = RemoteWorkspace if is_remote else EG.workspace
        self.workspace = workspace_init(
            repo_url,
            es=self.es_settings,
            index_prefix=self.settings['es.index_prefix'])
        if is_remote:
            self.workspace.im.sm = CachingRemoteStorageManager(repo_url)

    def parse_setting(self, name, default, parser):
        raw_value = self.settings.get(name, None)
        if raw_value is None:
            return default
        try:
            return parser(raw_value)
        except (TypeError, ValueError):
            return default

    def format_date(self, date_obj, fmt='%d %B %Y'):
        if isinstance(date_obj, datetime):
            return date_obj.strftime(fmt)

        try:
            dt = parser.parse(date_obj)
            return dt.strftime(fmt)
        except TypeError:
            return date_obj
        except ValueError:
            return date_obj

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

        return urljoin(image_host, image_url)

    def get_language_direction(self):
        language_code, _, country_code = self.locale.partition('_')
        if language_code in KNOWN_RTL:
            return "rtl"
        else:
            return "ltr"
