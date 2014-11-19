from elasticgit import EG
from dateutil import parser


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
