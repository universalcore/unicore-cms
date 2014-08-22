import pygit2
import shutil

from beaker.cache import cache_managers
from cms import utils
from gitmodel.workspace import Workspace

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

CACHE_TIME = 'long_term'


class AdminViews(object):

    def __init__(self, request):
        self.request = request

    def get_ws(self):
        repo_path = self.request.registry.settings['git.path']
        repo = pygit2.Repository(repo_path)
        if repo.is_empty:
            return Workspace(repo.path)
        return Workspace(repo.path, repo.head.name)

    @view_config(route_name='configure', renderer='cms:templates/admin/configure.pt')
    def configure(self):
        repo_path = self.request.registry.settings['git.path']
        ws = self.get_ws()
        utils.checkout_all_upstream(ws.repo)
        branches = utils.getall_branches(ws.repo)

        errors = []

        if self.request.method == 'POST':
            url = self.request.POST.get('url')
            if url:
                if ws.repo.is_empty:
                    shutil.rmtree(repo_path)
                    pygit2.clone_repository(url, repo_path)
                    self.get_ws().sync_repo_index()
            else:
                errors.append('Url is required')
        return {
            'repo': ws.repo,
            'errors': errors,
            'branches': [b.shorthand for b in branches],
            'current': ws.repo.head.shorthand if not ws.repo.is_empty else None
        }

    @view_config(route_name='configure_switch')
    def configure_switch(self):
        if self.request.method == 'POST':
            branch = self.request.POST.get('branch')
            if branch:
                self.get_ws().sync_repo_index()
                utils.checkout_branch(self.get_ws().repo, branch)
                self.get_ws().sync_repo_index()

                # clear caches
                for _cache in cache_managers.values():
                    _cache.clear()
        return HTTPFound(location=self.request.route_url('configure'))