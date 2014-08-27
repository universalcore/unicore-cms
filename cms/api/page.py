from cornice.resource import resource, view
from cms.api import validators, utils
from gitmodel.exceptions import DoesNotExist


@resource(
    collection_path='/api/pages.json',
    path='/api/pages/{uuid}.json'
)
class PageApi(utils.ApiBase):

    def collection_get(self):
        models = self.get_repo_models()

        primary_category_uuid = self.request.GET.get('primary_category', None)
        if primary_category_uuid:
            try:
                category = models.Category.get(primary_category_uuid)
                return [
                    p.to_dict()
                    for p in models.Page().filter(primary_category=category)
                ]
            except DoesNotExist:
                self.request.errors.add(
                    'api', 'DoesNotExist', 'Category not found.')
                return

        return [p.to_dict() for p in models.Page.all()]

    @view(renderer='json')
    def get(self):
        models = self.get_repo_models()

        uuid = self.request.matchdict['uuid']

        try:
            page = models.Page.get(uuid)
            return page.to_dict()
        except DoesNotExist:
            self.request.errors.add('api', 'DoesNotExist', 'Page not found.')
            return

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        models = self.get_repo_models()
        try:
            page = models.Page().get(uuid)
            models.Page.delete(
                uuid, True, message='Page delete: %s' % page.title)
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Page not found.')
