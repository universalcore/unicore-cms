import os
import pygit2

from cms.models import Page, Category
from cms import utils
from gitmodel.workspace import Workspace

from pyramid_beaker import set_cache_regions_from_settings
from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    set_cache_regions_from_settings(settings)
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.include('cms')
    return config.make_wsgi_app()


def init_repository(config):
    settings = config.registry.settings

    if not 'git.path' in settings:
        raise KeyError(
            'Please specify the git repo path '
            'e.g [app:main] git.path = %(here)s/repo/')

    repo_path = settings['git.path'].strip()

    try:
        repo = pygit2.Repository(repo_path)
    except:
        repo = pygit2.init_repository(repo_path, False)

    utils.checkout_all_upstream(repo)

    try:
        ws = Workspace(os.path.join(repo_path, '.git'), repo.head.name)
    except:
        ws = Workspace(os.path.join(repo_path, '.git'))

    ws.register_model(Page)
    ws.register_model(Category)


def includeme(config):
    config.include('pyramid_beaker')
    config.add_static_view('static', 'cms:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('categories', '/content/list/')
    config.add_route('category', '/content/list/{category}/')
    config.add_route('content', '/content/detail/{id}/')
    config.add_route('configure', '/admin/configure/')
    config.add_route('configure_switch', '/admin/configure/switch/')
    config.add_route('commit_log', '/admin/configure/log.json')
    config.scan()

    init_repository(config)
