from urlparse import urljoin
from datetime import datetime

from elasticgit import EG
from dateutil import parser
from libthumbor import CryptoURL


# known Right to Left language codes
KNOWN_RTL = set(["urd", "ara", "arc", "per", "heb", "kur", "yid"])


class BaseCmsView(object):

    def __init__(self, request):
        self.request = request
        self.locale = request.locale_name
        self.settings = request.registry.settings
        es_host = request.registry.settings.get(
            'es.host', 'http://localhost:9200')
        self.workspace = EG.workspace(
            es={'urls': [es_host]},
            workdir=self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'])

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
