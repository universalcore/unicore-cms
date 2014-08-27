from cornice import Service
from cms.api import validators, utils
from gitmodel.exceptions import DoesNotExist

page_service = Service(
    name='page_service',
    path='/api/pages.json',
    description="Manage pages"
)


@page_service.get()
def get_categories(request):
    models = utils.get_repo_models(request)

    uuid = request.GET.get('uuid', None)
    if uuid:
        try:
            category = models.Page().get(uuid)
            return category.to_dict()
        except DoesNotExist:
            request.errors.add('api', 'DoesNotExist', 'Page not found.')
            return
    return [c.to_dict() for c in models.Page().all()]
