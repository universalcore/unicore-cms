from elasticgit import EG
from dateutil import parser
from libthumbor import CryptoURL


class BaseCmsView(object):

    def __init__(self, request):
        self.request = request
        self.locale = request.locale_name
        self.settings = request.registry.settings
        self.workspace = EG.workspace(
            workdir=self.settings['git.path'],
            index_prefix=self.settings['es.index_prefix'])

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
