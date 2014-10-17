import shutil

from beaker.cache import cache_managers
from cms import utils
from cms.views.base import BaseCmsView

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

CACHE_TIME = 'long_term'

import warnings

warnings.warn('AdminViews seems to be completely missing test coverage.')


class AdminViews(BaseCmsView):

    @view_config(route_name='admin_home', renderer='templates/admin/home.pt')
    def home(self):
        return {}

    @view_config(route_name='commit_log', renderer='json')
    def get_commit_log(self):
        b = self.request.GET.get('branch')
        commits = self.workspace.repo.iter_commits(b, max_count=10)
        return [{
            'message': commit.message,
            'author': commit.author.name,
        } for commit in commits]

    def get_updates(self, branch=None):
        commits = utils.get_remote_updates_log(self.get_ws().repo, branch)

        return {
            'num_commits': len(commits),
            'new_commits': [
                {'message': c.message, 'author': c.author.name}
                for c in commits
            ]
        }

    @view_config(route_name='check_updates')
    def check_updates(self):
        utils.fetch(self.get_ws().repo)
        return HTTPFound(location=self.request.route_url('configure'))

    @view_config(route_name='get_updates', renderer='json')
    def get_updates_json(self):
        b = self.request.GET.get('branch')
        if not b:
            return {}
        return self.get_updates(b)

    @view_config(route_name='configure_fast_forward')
    def fast_forward(self):
        utils.fast_forward(self.get_ws().repo)
        return HTTPFound(location=self.request.route_url('configure'))

    @view_config(
        route_name='configure', renderer='cms:templates/admin/configure.pt')
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
                    # NOTE: pygit no longer being used
                    # pygit2.clone_repository(url, repo_path)
                    self.get_ws().sync_repo_index()
            else:
                errors.append('Url is required')
        context = {
            'single': len(branches) == 1,
            'repo': ws.repo,
            'errors': errors,
            'branches': [b.shorthand for b in branches],
            'current': ws.repo.head.shorthand if not ws.repo.is_empty else None
        }
        context.update(self.get_updates())
        return context

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
