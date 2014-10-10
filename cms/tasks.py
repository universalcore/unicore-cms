from celery.task import task
from cms import utils


@task(ignore_result=True, serializer='json')
def fastforward(repo_path):
    repo = utils.CmsRepo.read(repo_path)
    repo.fast_forward()
