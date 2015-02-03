import git
from elasticgit import EG

from pyramid_beaker import set_cache_regions_from_settings
from pyramid.config import Configurator
from pyramid.i18n import default_locale_negotiator

import logging
log = logging.getLogger(__name__)

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


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    set_cache_regions_from_settings(settings)
    config = Configurator(settings=settings)
    config.include('cms')
    config.configure_celery(global_config['__file__'])
    return config.make_wsgi_app()


def init_repository(config):
    settings = config.registry.settings

    if 'git.path' not in settings:
        raise KeyError(
            'Please specify the git repo path '
            'e.g [app:main] git.path = %(here)s/repo/')

    repo_path = settings['git.path'].strip()

    if 'git.content_repo_url' in settings \
            and settings['git.content_repo_url'] \
            and not EG.is_repo(repo_path):
        content_repo_url = settings['git.content_repo_url'].strip()
        log.info('Cloning repository: %s' % (content_repo_url,))
        git.Repo.clone_from(content_repo_url, repo_path)
        log.info('Cloned repository into: %s' % (repo_path,))

    try:
        EG.read_repo(repo_path)
        log.info('Using repository found in: %s' % (repo_path,))
    except git.InvalidGitRepositoryError:
        EG.init_repo(repo_path)
        log.info('Initialising repository in: %s' % (repo_path,))


def get_locale_with_fallbacks(locale_name):
    if locale_name is None:
        return None

    language_code, _, country_code = locale_name.partition('_')
    lang = LANGUAGE_FALLBACKS.get(language_code, language_code)
    country = COUNTRY_FALLBACKS.get(country_code, country_code)

    if lang != language_code:
        log.warning(
            'Invalid language_code used: %s' % language_code,
            extra={'stack': True})

    if country != country_code:
        log.warning(
            'Invalid country_code used: %s' % country_code,
            extra={'stack': True})

    return u'%s_%s' % (lang, country)


def locale_negotiator_with_fallbacks(request):
    locale_name = default_locale_negotiator(request)
    return get_locale_with_fallbacks(locale_name)


def includeme(config):
    config.include('pyramid_chameleon')
    config.include('pyramid_beaker')
    config.include("cornice")
    config.include("pyramid_celery")
    config.add_static_view('static', 'cms:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('search', '/search/')
    config.add_route('categories', '/content/list/')
    config.add_route('category', '/content/list/{category}/')
    config.add_route('content', '/content/detail/{uuid}/')
    config.add_route('locale', '/locale/')
    config.add_route('locale_change', '/locale/change/')
    config.add_route('locale_matched', '/locale/{language}/')
    config.add_route('flatpage', '/{slug}/')
    config.scan()
    config.set_locale_negotiator(locale_negotiator_with_fallbacks)

    init_repository(config)
