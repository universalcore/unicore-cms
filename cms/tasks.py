from celery.task import task

from elasticgit import EG
from unicore.content.models import Page, Category


@task(ignore_result=True, serializer='json')
def fastforward(repo_path, index_prefix):
    workspace = EG.workspace(repo_path, index_prefix=index_prefix)
    workspace.fast_forward()
    workspace.reindex(Page)
    workspace.reindex(Category)
