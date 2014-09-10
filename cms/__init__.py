import os
import pygit2

from cms.models import Page, Category
from cms import utils
from cms.admin import AdminViews
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
    config.include('pyramid_handlers')
    config.include("cornice")
    config.add_static_view('static', 'cms:static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('categories', '/content/list/')
    config.add_route('category', '/content/list/{category}/')
    config.add_route('content', '/content/detail/{uuid}/')
    config.add_handler(
        'admin_home', '/admin/', handler=AdminViews, action='home')
    config.add_handler('admin', '/admin/{action}', handler=AdminViews)
    config.add_route('configure_switch', '/admin/configure/switch/')
    config.add_route('check_updates', '/admin/configure/update/')
    config.add_route('configure_fast_forward', '/admin/configure/fastforward/')
    config.add_route('commit_log', '/admin/configure/log.json')
    config.add_route('get_updates', '/admin/configure/updates.json')
    config.scan()

    init_repository(config)
