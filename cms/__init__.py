import git
from elasticgit import EG

from pyramid_beaker import set_cache_regions_from_settings
from pyramid.config import Configurator

import logging
log = logging.getLogger(__name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    set_cache_regions_from_settings(settings)
    config = Configurator(settings=settings)
    config.include('cms')
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
        git.Repo.clone(content_repo_url, repo_path)
        log.info('Cloned repository into: %s' % (repo_path,))

    try:
        EG.read_repo(repo_path)
        log.info('Using repository found in: %s' % (repo_path,))
    except git.InvalidGitRepositoryError:
        EG.init_repo(repo_path)
        log.info('Initialising repository in: %s' % (repo_path,))


def includeme(config):
    config.include('pyramid_chameleon')
    config.include('pyramid_beaker')
    config.include("cornice")
    config.include("pyramid_celery")
    config.add_static_view('static', 'cms:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('categories', '/content/list/')
    config.add_route('category', '/content/list/{category}/')
    config.add_route('content', '/content/detail/{uuid}/')
    config.add_route('locale', '/locale/')
    config.add_route('flatpage', '/{slug}/')
    config.scan()

    init_repository(config)
