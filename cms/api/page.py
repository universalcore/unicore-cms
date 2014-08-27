from cornice import Service
from cms.api import validators, utils
from gitmodel.exceptions import DoesNotExist

page_service = Service(
    name='page_service',
    path='/api/pages.json',
    description="Manage pages"
)


@page_service.get()
def get_pages(request):
    models = utils.get_repo_models(request)

    uuid = request.GET.get('uuid', None)
    if uuid:
        try:
            category = models.Page.get(uuid)
            return category.to_dict()
        except DoesNotExist:
            request.errors.add('api', 'DoesNotExist', 'Page not found.')
            return

    primary_category_uuid = request.GET.get('primary_category', None)
    if primary_category_uuid:
        try:
            category = models.Category.get(primary_category_uuid)
            return [
                p.to_dict()
                for p in models.Page().filter(primary_category=category)
            ]
        except DoesNotExist:
            request.errors.add('api', 'DoesNotExist', 'Category not found.')
            return

    return [p.to_dict() for p in models.Page.all()]
