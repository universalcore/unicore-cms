import pygit2
from celery.task import task
from cms import utils


@task(ignore_result=True, serializer='json')
def fastforward(repo_path):
    repo = pygit2.Repository(repo_path)
    utils.fast_forward(repo)
