import pygit2
from gitmodel.workspace import Workspace


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

    if not branch_name is None:
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
            if not Workspace(repo.path).has_changes():
                # merge changes
                repo.merge(branch.target)
            # fast-forward
            repo.reset(branch.target, pygit2.GIT_RESET_HARD)
    # update repo working directory
    Workspace(repo.path).sync_repo_index()


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
            checkout_upstream(repo, branch)


def getall_branches(repo, mode=pygit2.GIT_BRANCH_LOCAL):
    branches = repo.listall_branches(mode)
    return [repo.lookup_branch(b, mode) for b in branches]
