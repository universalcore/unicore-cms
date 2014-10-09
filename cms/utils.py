import pygit2
import os

from gitmodel.workspace import Workspace

from unicore_gitmodels import models


def get_remote_branch(repo, branch_name=None):
    if not branch_name:
        branch_name = repo.head.shorthand

    branches = repo.listall_branches(pygit2.GIT_BRANCH_REMOTE)
    for b in branches:
        if b.endswith(branch_name):
            return b
    return None


def fetch(repo):
    for remote in repo.remotes:
        remote.fetch()


def get_remote_updates_log(repo, branch_name=None):
    remote_name = get_remote_branch(repo, branch_name)
    if remote_name is None:
        return []

    if branch_name is not None:
        local_branch = repo.lookup_branch(branch_name)
    else:
        local_branch = repo.head

    branch = repo.lookup_branch(remote_name, pygit2.GIT_BRANCH_REMOTE)

    analysis, pref = repo.merge_analysis(branch.target)
    if analysis & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
        return []

    if not analysis & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
        raise Exception('Unable to fastforward')

    num_commits = len(repo.diff(local_branch.name, branch.name))

    commits = []
    if num_commits > 0:
        for commit in repo.walk(branch.target, pygit2.GIT_SORT_TIME):
            commits.append(commit)

            if len(commits) == num_commits:
                break

    return commits


def fast_forward(repo):
    for remote in repo.remotes:
        remote.fetch()
        remote_name = get_remote_branch(repo)
        if remote_name is None:
            continue

        branch = repo.lookup_branch(remote_name, pygit2.GIT_BRANCH_REMOTE)
        if branch.target.hex != repo.head.target.hex:
            if not get_workspace(repo).has_changes():
                # merge changes
                repo.merge(branch.target)
            # fast-forward
            repo.reset(branch.target, pygit2.GIT_RESET_HARD)
    # update repo working directory
    get_workspace(repo).sync_repo_index()


def checkout_upstream(repo, branch):
    name = branch.split('/')[1]
    remote = repo.lookup_branch(branch, pygit2.GIT_BRANCH_REMOTE)
    master = repo.create_branch(name, repo[remote.target.hex])
    master.upstream = remote


def checkout_branch(repo, name):
    branch = repo.lookup_branch(name)
    if not branch:
        checkout_upstream(repo, name)
        branch = repo.lookup_branch(name)
    ref = repo.lookup_reference(branch.name)
    repo.checkout(ref)


def checkout_all_upstream(repo):
    for branch in repo.listall_branches(pygit2.GIT_BRANCH_REMOTE):
        name = branch.split('/')[1]

        if name == 'HEAD':
            continue

        if not repo.lookup_branch(name):
            checkout_upstream(repo, branch)


def getall_branches(repo, mode=pygit2.GIT_BRANCH_LOCAL):
    branches = repo.listall_branches(mode)
    return [repo.lookup_branch(b, mode) for b in branches]


def get_workspace(repo):
    try:
        ws = Workspace(repo.path, repo.head.name)
    except pygit2.GitError:
        ws = Workspace(repo.path)

    return ws


class CmsRepoException(Exception):
    pass


class CmsRepo(object):

    WORKSPACE_CACHE = {}

    @classmethod
    def cache(cls, cms_repo):
        cls.WORKSPACE_CACHE[cms_repo.repo.path] = cms_repo
        return cms_repo

    @classmethod
    def is_cached(cls, repo_path):
        return repo_path in cls.WORKSPACE_CACHE

    @classmethod
    def read_from_cache(cls, repo_path):
        return cls.WORKSPACE_CACHE[repo_path]

    @classmethod
    def expire(cls, cms_repo):
        del cls.WORKSPACE_CACHE[cms_repo.repo.path]

    @classmethod
    def clear_cache(cls):
        for repo in cls.WORKSPACE_CACHE.values():
            cls.expire(repo)

    @classmethod
    def exists(self, repo_path):
        return os.path.exists(repo_path)

    @classmethod
    def init(cls, repo_path, name, email, bare=False,
             commit_message='Initialising repository.'):
        repo = pygit2.init_repository(repo_path, bare)
        author = pygit2.Signature(name, email)
        committer = author
        tree = repo.TreeBuilder().write()
        repo.create_commit(
            'refs/heads/master',
            author, committer, commit_message, tree, [])
        cms_repo = cls.read(repo_path, cached=False)
        cms_repo.checkout_all_upstream()
        return cms_repo

    @classmethod
    def clone(cls, repo_url, repo_path):
        return cls(pygit2.clone_repository(repo_url, repo_path))

    @classmethod
    def read(cls, repo_path, cached=True):
        if cached and cls.is_cached(repo_path):
            return cls.read_from_cache(repo_path)

        if not cls.exists(repo_path):
            raise CmsRepoException('Path %s does not exist.' % (repo_path,))
        repo = cls(pygit2.Repository(repo_path))
        return cls.cache(repo)

    def __init__(self, repo):
        self.repo = repo
        self._workspace = get_workspace(self.repo)
        self._workspace.import_models(models)

    def expire_cache(self):
        return self.__class__.expire(self)

    def get_remote_branch(self, branch_name=None):
        return get_remote_branch(self.repo, branch_name=branch_name)

    def fetch(self):
        return fetch(self.repo)

    def get_remote_updates_log(self, branch_name=None):
        return get_remote_updates_log(self.repo, branch_name=branch_name)

    def fast_forward(self):
        self.expire_cache()
        return fast_forward(self.repo)

    def checkout_upstream(self, branch):
        return checkout_upstream(self.repo, branch)

    def checkout_branch(self, name):
        return checkout_branch(self.repo, name)

    def checkout_all_upstream(self):
        return checkout_all_upstream(self.repo)

    def getall_branches(self, mode=pygit2.GIT_BRANCH_LOCAL):
        return getall_branches(self.repo, mode=mode)

    def get_workspace(self):
        return self._workspace

    def get_models(self):
        return self.get_workspace().models
