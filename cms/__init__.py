import os
import pygit2

from pyramid.config import Configurator
from gitmodel.workspace import Workspace
from cms.models import Page, Category


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.scan()

    repo_path = settings['git.path'].strip()
    pygit2.init_repository(repo_path, False)

    ws = Workspace(os.path.join(repo_path, '.git'))
    ws.register_model(Page)
    ws.register_model(Category)

    return config.make_wsgi_app()
