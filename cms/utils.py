import pygit2
from gitmodel.workspace import Workspace


def get_remote_branch(repo):
    branches = repo.listall_branches(pygit2.GIT_BRANCH_REMOTE)
    for b in branches:
        if b.endswith(repo.head.shorthand):
            return b
    return None


def fetch(repo):
    ws = Workspace(repo.path)
    for remote in repo.remotes:
        remote.fetch()


def get_remote_updates_log(repo):
    num_commits, pref = repo.merge_analysis(repo.head.target)
    remote_name = get_remote_branch(repo)
    if remote_name is None:
        return []

    branch = repo.lookup_branch(remote_name, pygit2.GIT_BRANCH_REMOTE)
    commits = []
    for commit in repo.walk(branch.target, pygit2.GIT_SORT_TIME):
        commits.append(commit)

        if len(commits) == num_commits:
            break

    return commits


def fastforward(repo):
    ws = Workspace(repo.path)
    for remote in repo.remotes:
        remote.fetch()
        remote_name = get_remote_branch(repo)
        if remote_name is None:
            continue

        branch = repo.lookup_branch(remote_name, pygit2.GIT_BRANCH_REMOTE)
        if branch.target.hex != repo.head.target.hex:
            if not ws.has_changes():
                # merge changes
                repo.merge(branch.target)
            # fast-forward
            repo.reset(branch.target, pygit2.GIT_RESET_HARD)
    # update repo working directory
    ws.sync_repo_index()


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
    #fastforward(repo)
    for branch in repo.listall_branches(pygit2.GIT_BRANCH_REMOTE):
        name = branch.split('/')[1]

        if name == 'HEAD':
            continue

        if not repo.lookup_branch(name):
            print '%s not found. creating from remote' % name
            checkout_upstream(repo, branch)


def getall_branches(repo, mode=pygit2.GIT_BRANCH_LOCAL):
    branches = repo.listall_branches(mode)
    return [repo.lookup_branch(b, mode) for b in branches]
