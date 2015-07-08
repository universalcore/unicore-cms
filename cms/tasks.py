from pyramid_celery import celery_app as app

from elasticgit import EG
from elasticgit.storage import RemoteStorageManager

from cms.views.utils import is_remote_repo_url


@app.task(ignore_result=True)
def pull(repo_url, index_prefix, es=None):
    if is_remote_repo_url(repo_url):
        sm = RemoteStorageManager(repo_url)
        sm.pull()
    else:
        workspace = EG.workspace(repo_url, index_prefix=index_prefix, es=es)
        workspace.pull()
