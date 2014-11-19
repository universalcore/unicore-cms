from elasticgit import EG
from dateutil import parser


class BaseCmsView(object):

    # NOTE
    # Swahili code `swh` is not ISO639-2 so we need to correct this
    # and use `swa` instead.
    LANGUAGE_FALLBACKS = {
        'swh': 'swa',
    }

    # NOTE
    # United Kingdom code `UK` is not ISO3166 so we need to correct this
    # and use `GB` instead.
    COUNTRY_FALLBACKS = {
        'UK': 'GB',
    }

    def __init__(self, request):
        self.request = request
        self.locale = self.get_locale_with_fallbacks(request.locale_name)
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

    def get_locale_with_fallbacks(self, locale_name):
        language_code, _, country_code = locale_name.partition('_')
        lang = self.LANGUAGE_FALLBACKS.get(language_code, language_code)
        country = self.COUNTRY_FALLBACKS.get(country_code, country_code)
        return u'%s_%s' % (lang, country)
