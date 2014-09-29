import os
import pygit2

from unicore_gitmodels import models
from cms import utils

from pyramid_beaker import set_cache_regions_from_settings
from pyramid.config import Configurator


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
            and not os.path.exists(repo_path):
        content_repo_url = settings['git.content_repo_url'].strip()
        pygit2.clone_repository(content_repo_url, repo_path)

    try:
        repo = pygit2.Repository(repo_path)
    except KeyError:
        repo = pygit2.init_repository(repo_path, False)

    utils.checkout_all_upstream(repo)

    ws = utils.get_workspace(repo)

    ws.register_model(models.GitPageModel)
    ws.register_model(models.GitCategoryModel)


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
    config.add_route('admin_home', '/admin/')
    config.add_route('configure', '/admin/configure/')
    config.add_route('configure_switch', '/admin/configure/switch/')
    config.add_route('check_updates', '/admin/configure/update/')
    config.add_route('configure_fast_forward', '/admin/configure/fastforward/')
    config.add_route('commit_log', '/admin/configure/log.json')
    config.add_route('get_updates', '/admin/configure/updates.json')
    config.add_route('locale', '/locale/')
    config.add_route('flatpage', '/{slug}/')
    config.scan()

    init_repository(config)
