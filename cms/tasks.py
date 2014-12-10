from celery.task import task

from elasticgit import EG
from unicore.content.models import Page, Category, Localisation
from UniversalAnalytics import Tracker


@task(ignore_result=True, serializer='json')
def fastforward(repo_path, index_prefix):
    workspace = EG.workspace(repo_path, index_prefix=index_prefix)
    workspace.fast_forward()
    workspace.reindex(Page)
    workspace.reindex(Category)
    workspace.reindex(Localisation)


@task(ignore_result=True, serializer='json')
def send_ga_pageview(
        profile_id, client_id, path, uip, referer, domain, user_agent):
    tracker = Tracker.create(
        profile_id, client_id=client_id, user_agent=user_agent)
    tracker.send('pageview', path=path, uip=uip, dr=referer, dh=domain)
